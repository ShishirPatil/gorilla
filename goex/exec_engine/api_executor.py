"""This module will execute API calls and their reversals."""

import subprocess
import json
from exec_engine.db_manager import DBManager

from exec_engine.credentials.credentials_utils import creds_from_prompt, CREDS_FOLDER_PATH
from exec_engine.docker_sandbox import *

from exec_engine.utils import RESTful_Type
from exec_engine.pipeline import generate_reverse_command
from exec_engine.negation_manager import NegationAPIPairManager, NaiveNegationAPIPairManager

from pathlib import Path

CUR_DIR = os.path.dirname(Path(os.path.realpath(__file__)))

def code_add_dummy_argument(python_code):
    dummy_args = json.load(open('./function/dummy_key.json', 'r'))
    for dummy_args_key in dummy_args:
        if isinstance(dummy_args[dummy_args_key], str):
            dummy_args[dummy_args_key] = "\"" + dummy_args[dummy_args_key] + "\""
        python_code = python_code.replace("\"<<"+dummy_args_key+"_placeholder>>\"", dummy_args[dummy_args_key])
    return python_code

class APIExecutor:
    """Base Class for all API executors

    Should be stateless and should not have any attributes.

    Attributes:
        None
    
    Methods:
        execute_api_call: Execute API call
    """
    def __init__(self):
        return None
    
    def execute_api_call(self, command: str) -> int:
        """Execute API call.
        
        Args:
            command (str): API call to execute.
        """
        raise NotImplementedError
    
    def set_execution_environment(self, env, docker_sandbox: DockerSandbox = None):
        if env == "local":
            self.env = "local"
            return
        elif env == "docker":
            self.env = "docker"
            self.docker_client = "docker_client"
            return
        else:
            print('env can only be set to "docker" or "local"')

class PythonAPIExecutor(APIExecutor):
    """Executes Python API calls
    
    Methods:
        execute_api_call: Execute API call
    """
    def __init__(self, docker_sandbox: DockerSandbox = None, negation_manager: NaiveNegationAPIPairManager = None, path: str = CUR_DIR):
        self.env = None
        self.docker_sandbox = docker_sandbox
        if negation_manager != None:
            self.negation_manager = negation_manager(path)
        else:
            self.negation_manager = None

    def prepare_credentials(self, prompt:str, technique="lut"):
        credentials = creds_from_prompt(prompt, CREDS_FOLDER_PATH, technique)
        try:
            services = [service_name for service_name, value, file_type in credentials]
        except:
            raise Exception("Error: credentials have to be passed in as a list of [service_name, value, cred_type] pairs")
        return credentials, services
    
    # try_get_backward_call will try to see if there is a corresponding backward call for the input forward call
    # if not, it will prompt the LLM to come up with one
    def try_get_backward_call(self, forward_call, prompt, credentials, api_type, generate_mode='default', model="gpt-4-turbo-preview"):
        if self.negation_manager != None:
            # look up if there is a corresponding backward call in reverse_db
            negation_call = self.negation_manager.get_success(forward_call)
            if negation_call != None:
                return negation_call
            
        return generate_reverse_command(forward_call, prompt, credentials, api_type, generate_mode, openai_model=model)

    def execute_api_call(self, command: str, credentials: list = None) -> int:
        """Execute API call.
        
        Args:
            command (str): API call to execute.
        """
        image_id = self.docker_sandbox.create_image_from_code(command)
        if image_id == None:
            raise Exception("Error: failed to generate or get image id")
        # Add dummy arguments to the code
        command = code_add_dummy_argument(command)
        result = self.docker_sandbox.create_python_sandbox(command, image_id, credentials=credentials)

        return result
