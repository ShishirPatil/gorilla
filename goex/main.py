"""The driver file for the program."""

import re
import os
from typing import Union
from collections import deque
from pathlib import Path

from exec_engine.db_manager import DBManager
from exec_engine.api_executor import APIExecutor, PythonAPIExecutor
from exec_engine.docker_sandbox import DockerSandbox
from exec_engine.fs_manager import FSManager
from exec_engine.utils import SQL_Type, RESTful_Type, Filesystem_Type

from exec_engine.pipeline import generate_command

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)))
CHECKPOINTS_FOLDER_PATH = os.path.join(ROOT_FOLDER_PATH, "docker/mysql_docker/checkpoints")

class ExecutionEngine:
    """Can identify and execute API calls and their reversals."""

    def __init__(self, history_length: int = 10, path=None, generate_mode='default'):
        # Keys for LLMs
        self.openai_api_key = None
        self.anthropic_api_key = None
        # Initialize the instances of the classes
        self.api_executor = APIExecutor()
        self.docker_sandbox = DockerSandbox()
        
        self.fs_initialized = False
        self.db_initialized = False
        self.path = path
        self.generate_mode = generate_mode

        # Dry Run is option 2, no dry run is option 1, user can specify which types to dry-run
        self.dry_run_dict = {
            SQL_Type: False,
            Filesystem_Type: False,
            RESTful_Type: False,
        }

        # Initialize the API and ~API pair circular queue
        self.api_history_pair_queue_dict = {
            SQL_Type: deque(maxlen=history_length),
            Filesystem_Type: deque(maxlen=history_length),
            RESTful_Type: deque(maxlen=history_length),
        }

    def gen_api_pair(self, input_prompt: str, api_type: str, credentials, model) -> list:
        """Generate an API call and its reversal"""
        if api_type == RESTful_Type:
            forward_call = generate_command(input_prompt, credentials, generate_mode=self.generate_mode, openai_model=model)
            backward_call = self.api_executor.try_get_backward_call(forward_call, input_prompt, credentials, api_type,
                                                                     generate_mode=self.generate_mode, model=model)
            return forward_call, backward_call
            
        elif api_type == SQL_Type:
            input_p = self.db_manager.task_to_prompt(input_prompt)
            forward_call = generate_command(input_p, credentials, api_type=SQL_Type, generate_mode=self.generate_mode, openai_model=model)

            reverse_p = self.db_manager.task_to_prompt(forward_call, forward=False)
            backward_call = generate_command(reverse_p, credentials, api_type=SQL_Type, generate_mode=self.generate_mode, openai_model=model)
            return forward_call, backward_call

        elif api_type == Filesystem_Type:
            input_p = self.fs_manager.task_to_prompt(input_prompt)
            forward_call = generate_command(input_p, credentials, api_type=Filesystem_Type, generate_mode=self.generate_mode, openai_model=model)

            reverse_p = self.fs_manager.task_to_prompt(forward_call, forward=False)
            backward_call = generate_command(reverse_p, credentials, api_type=Filesystem_Type, generate_mode=self.generate_mode, openai_model=model)
            return forward_call, backward_call
        raise NotImplementedError


    def run_prompt(self, input_prompt: str, api_type: str):
        credentials = None          # TODO: Work out credentials logic
        api_call, neg_api_call = self.gen_api_pair(input_prompt, api_type, credentials, model="gpt-4-turbo-preview")

        exec_result = self.exec_api_call(api_call, api_type, neg_api_call)


    def test_api_pair_on_docker(self, api_call, neg_api_call, api_type, environment=None) -> bool:
        """Tests an API call and its negation by executing them in a sandbox and verifying the state reversion."""

        if api_type != SQL_Type and api_type != Filesystem_Type:
            # 1. Create Docker sandbox
            sandbox = self.docker_sandbox.create_sandbox()
            # 2. Execute API call and its reversal in the sandbox
            self.api_executor.execute_api_call(api_call)
            self.api_executor.execute_api_call(neg_api_call)
            # 3. Check if the state is reverted successfully
            success = self.check_state_reversion()
            # 4. Log the result in the database
            self.db_manager.log_api_pair(api_call, neg_api_call, success)
            # 5. Delete the sandbox
            self.docker_sandbox.delete_sandbox(sandbox)
        elif api_type == SQL_Type:
            
            test_prompt = "Table Schemas:\n"
            test_prompt += self.db_manager.get_schema_as_string()
            test_prompt += f"\nSQL call: {api_call}\n"
            test_prompt += f"Reverse call: {neg_api_call}\n\n"
            test_prompt += "Given the table schemas, SQL call, and its reversal call, " + \
            "write a Python script to test the SQL call to see if the reversal works. " + \
            "To test, create a new bare minimum database to test this out for " + \
            f"{self.db_manager.db_type}, run the SQL call and its reversal, and check " + \
            "that the start state and the end state are the same. Print out only True " + \
            "if it works, otherwise print out False and print the table contents to stderr. Don't print anything else."

            if self.db_manager.TEST_CONFIG:
                test_prompt += f"Make sure to use the config to access the DB: {self.db_manager.TEST_CONFIG}"


        elif api_type == Filesystem_Type:
            test_prompt = (
                "Path: /sandbox/test_dir"
                f"Shell Command: {api_call}"
                f"Reverse Command: {neg_api_call}"
                "Given a directory path, and a shell command and the reverse command of the shell command, " 
                "can you write a python script to test that the reverse command properly reverses the shell command? "
                "Duplicate the given directory, and perform execution in the duplicate directory only. "
                "Print out only True if it works, otherwise print out False and print errors to stderr. Don't print anything else.\n\n"
            )

            
        res = generate_command(test_prompt, generate_mode=self.generate_mode)

        # get script
        result = self._run_code_in_container(code=res, debug=True, api_type=api_type)

        if not result:
            return False
        
        out, debug = result['output'], result['debug']
        if len(out) >= 1:
            revert_success = bool(out[-1])
            return revert_success
        else:
            print(f"An issue occurred during the dry run: {debug}")
            return False

    def exec_api_call(self, api_call: str, api_type, debug_neg: str = None) -> str:

        if debug_neg:
            neg_api_call = debug_neg


        if self.dry_run_dict[api_type] and debug_neg:
            revert_success = self.test_api_pair_on_docker(api_call, neg_api_call, api_type)
            if not revert_success:
                raise RuntimeError("Dry Run Failed")
            
        if api_type == RESTful_Type:
            self._exec_restful_call(api_call)
            
            payload = (api_call, neg_api_call)

        else:
            payload = (api_call, debug_neg)
            if api_type == SQL_Type:
                if self.db_manager:
                    self._exec_db_call(api_call)
                else:
                    payload = None
            elif api_type == Filesystem_Type:
                self._exec_filesystem_call(api_call)
            
        if payload:
            self._add_api_reverse_to_queue(api_type, payload)

    def undo_api_call(self, api_type: Union[SQL_Type, Filesystem_Type, RESTful_Type], services=None, option=2):
        api_call, neg_api_call = self._pop_api_reverse_from_queue(api_type)

        if not api_call:
            print('History is empty')
            return

        if option == 2:
            # Not a RESTful API negation pair, transaction based
            self._undo_transaction(api_type)

        else:
            if api_type == RESTful_Type:
                self.api_executor.execute_api_call()


    def commit_api_call(self, api_type, arg=None):
        if api_type != RESTful_Type:
            self._commit_transaction(api_type, message=arg)
        else:
            raise NotImplementedError
        self._reset_api_history_queue(api_type)

    def _undo_transaction(self, api_type):
        if api_type == SQL_Type:
            self.db_manager.rollback_db_calls()
        elif api_type == Filesystem_Type:
            self.fs_manager.revert()
        else:
            raise NotImplementedError
        
    def _commit_transaction(self, api_type, message=None):
        if api_type == SQL_Type:
            self.db_manager.commit_db_calls()
        elif api_type == Filesystem_Type:
            if not message:
                message = 'Auto-commit via FSManager'
            self.fs_manager.commit(message=message)
                
        else:
            raise NotImplementedError
        
    def initialize_db(self, debug_manager: DBManager=None):
        print('Initialized DB Manager')
        self.db_manager = debug_manager
        self.db_initialized = True

    def initialize_fs(self, debug_path=None, git_init=True):
        print('Initialized FS Manager')
        self.fs_manager = FSManager(debug_path, git_init=git_init)
        self.fs_manager.initialize_version_control()
        self.fs_initialized = True

    def set_dry_run(self, api_type, on):
        self.dry_run_dict[api_type] = on

    def _exec_db_call(self, call) -> bool:
        """Execute a SQL API call"""
        if not self.db_initialized:
            self.initialize_db()
            
        if re.match(
            r"^SELECT\b", call, re.IGNORECASE
        ):
            return self.db_manager.fetch_db_call(call)
        else:
            self.db_manager.execute_db_call(call)

    def _exec_filesystem_call(self, call) -> bool:
        """Execute a file system API call"""
        if not self.fs_initialized:
            self.initialize_fs()
            self.fs_manager.initialize_version_control()  # make sure that git exists on every call
        self.fs_manager.execute(call, display=True)

    def _exec_restful_call(self, call) -> bool:
        """Execute a RESTful API call"""
        raise NotImplementedError

    def _add_api_reverse_to_queue(self, api_type: Union[SQL_Type, Filesystem_Type, RESTful_Type], payload):
        self.api_history_pair_queue_dict[api_type].append(payload)

    def _pop_api_reverse_from_queue(self, api_type: Union[SQL_Type, Filesystem_Type, RESTful_Type]):
        """Remove a pair of API calls from the list of API pairs"""
        # Dequeue in deque
        return self.api_history_pair_queue_dict[api_type].pop() if self.api_history_pair_queue_dict[api_type] else None

    def _reset_api_history_queue(self, api_type: Union[SQL_Type, Filesystem_Type, RESTful_Type]):
        """Reset the API history queue"""
        # Clear the deque
        self.api_history_pair_queue_dict[api_type].clear()

    def _run_code_in_container(self, code, debug=False, api_type=RESTful_Type):
        try:
            volume_path = None
            if api_type == Filesystem_Type:
                volume_path = os.path.abspath(self.fs_manager.fs_path)
            image = self.docker_sandbox.create_image_from_code(code, api_type)
            response = self.docker_sandbox.create_python_sandbox(code, image, attached_volume=volume_path)
            
            if not debug:
                return response['output']
            else:
                return response
        except Exception as e:
            print("An error occured while trying to execute output locally {e}.\nAborted...".format(e=e))
            return
