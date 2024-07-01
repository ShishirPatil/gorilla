import argparse
from simple_colors import *
from exec_engine.pipeline import *
from exec_engine.credentials.credentials_utils import *
from halo import Halo

import os
from pathlib import Path
from authorizations.scripts.authorization_utils import authorize_service
from main import ExecutionEngine, PythonAPIExecutor

from exec_engine.utils import SQL_Type, Filesystem_Type
from exec_engine.db_manager import MySQLManager, SQLiteManager
from dotenv import load_dotenv
import questionary


GORILLA_EMOJI = "🦍 " 
SUCCESS = u'\u2713'
USER_CONFIG_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__))), "user_config.json")
default_config = {'max_attempt' : 1,
                  'option': 2,
                  'show_debug': True,
                  'model': "gpt-4-turbo-preview",
                  'undo': True,
                  'dbtype': 'sqlite',
                  'lfs_limit': 200,
                  'fs_path': ""
                  }

def insert_callback(service, key):
    print(SUCCESS)
    with Halo(text=f"{GORILLA_EMOJI}inserting creds...", spinner="dots"):
        insert_creds(service, key, target = CREDS_FOLDER_PATH, cred_type="raw")

def list_callback():
    print(list_creds(target = CREDS_FOLDER_PATH))

def restful_callback(prompt, generate_mode):
    engine = ExecutionEngine(generate_mode=generate_mode)
    # Specify a negation manager (e.g NaiveNegationAPIPairManager) when 
    # initializing PythonAPIExecutor to record the user feedback for the negated API
    engine.api_executor = PythonAPIExecutor(engine.docker_sandbox) 
    creds, services = engine.api_executor.prepare_credentials(prompt)
    
    if not creds:
        for service in list_supported_services():
            if service in prompt:
                print('Warning: detect keyword {service} but {service} has not been authorized'.format(service=service))

    if not services:
        api_string_extension = ""
    else:
        api_string_extension = "from {services} API...".format(services=services)
    with Halo(text=f"{GORILLA_EMOJI}fetching response {api_string_extension}".format(api_string_extension), spinner="dots"):
        response, forward_call, backward_call = prompt_execute(
            engine, prompt, services=services, creds=creds, max_attempt=get_config('max_attempt'), model=get_config('model'))
        if response['output']:
            print('\n', '\n'.join(response["output"][0]))
        else:
            print('\n', "execution failed with the following debug messages:")
            print('\n', response['debug'])
            return

    if default_config["undo"]:
        answer = questionary.select("Are you sure you want to keep the changes", choices=["Commit", "Undo"]).ask()
        
        if answer.lower() == "undo":
            # if there is a match with print_pattern, it's highly likely that it is only a print message
            print_pattern = r'^\s*print\s*\((?:.|\n)*\)\s*$'
            matches = re.search(print_pattern, backward_call, re.DOTALL)
            if matches:
                print(engine.api_executor.execute_api_call(backward_call, services)["output"])
            else:
                print("Warning: the undo feature is still in beta mode and may cause irreversible changes\n" +
                    "Gorilla will execute the following code:\n{}".format(backward_call))
                confirmation = questionary.select("", choices=["Confirm Undo", "Cancel Undo"]).ask()
            
                if confirmation == "Confirm Undo":
                    print(engine.api_executor.execute_api_call(backward_call, services)["output"])
                else:
                    print("Abort undo, execution completed!")
                
            if engine.api_executor.negation_manager != None:
                feedback = questionary.select("How would you rate the suggested negation API?", 
                                              choices=["Correct", "Incorrect", "Skip"]).ask()

                if feedback == "Correct":
                    engine.api_executor.negation_manager.insert_log(forward_call, backward_call, True)
                elif feedback == "Incorrect":
                    engine.api_executor.negation_manager.insert_log(forward_call, backward_call, False)
    print("Execution Completed!")

def initialize_user_config():
    if os.path.exists(USER_CONFIG_PATH):
        return
    with open(USER_CONFIG_PATH, 'w') as j:
        json.dump(default_config, j)
    print("Config file created successfully.")

def update_user_config(key, value):
    with open(USER_CONFIG_PATH, 'r') as j:
        oldconfig = json.load(j)
    if key == 'max_attempt' or key == 'option' or key == 'lfs_limit':
        value = int(value)
    elif key == 'show_debug':
        value = value.lower() == 'true'
    elif key == 'fs_path':
        value = os.path.join(os.getcwd(), value)
        if not os.path.exists(value) and not os.path.isdir(value):
            print("Please make sure you enter a valid directory path!")
            return
    modified = False
    if oldconfig[key] != value:
        modified = True
        oldconfig[key] = value
    if modified:
        with open(USER_CONFIG_PATH, 'w') as j:
            json.dump(oldconfig, j)
            print("Config file modified successfully.")

def get_config(key):
    with open(USER_CONFIG_PATH, 'r') as j:
        config = json.load(j)
    return config[key]

def authorize_callback(services):
    supported_services = list_supported_services()
    for service in services:
        if service in supported_services:
            try:
                authorize_service(service)
            except Exception as e:
                print(e)
                print("Failed to authorize user's {service} account".format(service=service))
        else:
            print("{service} is currently not supported".format(service=service))

def fs_callback(prompt, generate_mode):
    path = get_config('fs_path')
    if not path:
        path = os.getcwd()
    path = os.path.abspath(path)

    engine = ExecutionEngine(path=path, generate_mode=generate_mode)
    option = get_config('option')
    engine.initialize_fs(debug_path=path, git_init=option == 2)

    if option == 1:
        engine.set_dry_run(Filesystem_Type, True)
    else:
        engine.set_dry_run(Filesystem_Type, False)
    
    api_call, neg_api_call = engine.gen_api_pair(prompt, Filesystem_Type, None, model=get_config('model'))
    print(black("Do you want to execute the following filesystem command...", 'bold') + '\n' + magenta(api_call, 'bold'))
    answer = questionary.select("", 
                                choices=["Yes", "No"]).ask()
    if answer == "No":
        print("Execution abandoned.")
        return
    
    try:                                                                            
        engine.exec_api_call(api_call=api_call, api_type=Filesystem_Type, debug_neg=neg_api_call)
    except RuntimeError as e :
        print(f"Execution Failed: {e}")
        return  

    option_to_method = {
            1: 'negation call',
            2: 'git reset'
        }
    answer = questionary.select("Are you sure you want to keep the changes", 
                                choices=["Commit", "Undo" + " ({})".
                                            format(option_to_method[option])]).ask()

    if option == 2:    
        if answer == "Commit":
            commit_msg = questionary.text("Enter a commit message [Optional]: ").ask()
            engine.commit_api_call(Filesystem_Type, commit_msg)
            print("Execution commited.")
        else:
            engine.undo_api_call(Filesystem_Type, option=option)
            print("Execution undone.")
    else:
        if answer == "Commit":
            print("Execution completed.")
        else:
            engine.exec_api_call(neg_api_call, api_type=Filesystem_Type)
            print("Execution undone.")
            
def remove_creds_callback(services):
    try:
        remove_creds(services)
    except Exception as e:
        print(e)
        print("An unexpected error occured while removing credentials")

def db_callback(prompt, generate_mode):
    config = {
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME'),
        'path': os.environ.get('DATABASE_PATH')
        }
        
    engine = ExecutionEngine(generate_mode=generate_mode)

    db_type = get_config('dbtype')
    db_manager = None
    try:
        if db_type == 'mysql':
            db_manager = MySQLManager(config, docker_sandbox=engine.docker_sandbox)
        elif db_type == 'sqlite':
            db_manager = SQLiteManager(config, docker_sandbox=engine.docker_sandbox)
    except Exception as e:
        print(f"Error during {db_type} Manager Init: {e}")
        return
    db_manager.connect()

    option = get_config('option')
    if option == 1:
        engine.set_dry_run(SQL_Type, True)
    else:
        engine.set_dry_run(SQL_Type, False)

    engine.initialize_db(debug_manager=db_manager)
    api_call, neg_api_call = engine.gen_api_pair(prompt, SQL_Type, None, model=get_config('model'))
    if neg_api_call == None and option == 1:
        print("Error: option 1 requires negation API call. neg_api_call is None.")
        return
    print(black("Do you want to execute the following database command...", 'bold') + '\n' + magenta(api_call, 'bold'))
    answer = questionary.select("", 
                                choices=["Yes", "No"]).ask()
    if answer == "No":
        print("Execution abandoned.")
        return
    
    try:                                                                            
        engine.exec_api_call(api_call=api_call, api_type=SQL_Type, debug_neg=neg_api_call)
        if option == 1:
            engine.commit_api_call(SQL_Type)
    except RuntimeError as e :
        print(f"Execution Failed: {e}")
        return  


    option_to_method = {
            1: 'negation call',
            2: 'db rollback'
        }
    answer = questionary.select("Are you sure you want to keep the changes", 
                                choices=["Commit", "Undo" + " ({})".
                                            format(option_to_method[option])]).ask()

    if option == 2:    
        if answer == "Commit":
            engine.commit_api_call(SQL_Type)
            print("Execution commited.")
        else:
            engine.undo_api_call(SQL_Type, option=option)
            print("Execution undone.")
    else:
        if answer == "Commit":
            print("Execution completed!")
        else:
            engine.exec_api_call(neg_api_call, api_type=SQL_Type)
            engine.commit_api_call(SQL_Type)
            print("Execution undone.")


def exit_with_help_message(parser):
    print(green("To execute a prompt with a specified execution type", ['bold']))
    # retrieve subparsers from parser
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
    # there will probably only be one subparser_action,
    # but better save than sorry
    for subparsers_action in subparsers_actions:
        # get all subparsers and print help
        for choice, subparser in subparsers_action.choices.items():
            print(subparser.format_help())

    print(green("To perform other Gorilla-x operations", ['bold']))
    parser.print_help()

    parser.exit()

class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        exit_with_help_message(parser)

class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        exit_with_help_message(self)


def main():
    initialize_user_config()
    parser = ArgumentParser(add_help=False)
    subparser = parser.add_subparsers(dest='command')

    execute_parser = subparser.add_parser("execute", add_help=False)
    execute_parser.add_argument("-prompt", nargs='*', metavar='prompt', help="prompt for Gorilla-x to execute")
    execute_parser.add_argument("-type", nargs=1, metavar='type', help="specify the execution type as either 'rest', 'db', or 'fs'")
    execute_parser.add_argument("-generate_mode", metavar='gen_mode', help="specify how to use the LLM, either 'default', 'function_in_context' or 'function_calling_native'", default='default')

    parser.add_argument('--help', action=_HelpAction)
    parser.add_argument('-insert_creds', action='store', metavar=('service', 'key'), nargs=2, help="Inserts the service-key pair to Gorilla's secret store.")
    parser.add_argument('-list_creds', action='store_true', help="Lists all the currently registered credentials.")
    parser.add_argument('-authorize', action='store', metavar='service', nargs=1, help="Perform OAuth2 authorization and retrieve access token from the service")
    parser.add_argument('-remove_creds', action='extend', metavar='service', nargs="+", help="Removes previously authorized credentials. Enter ALL as parameter to delete all creds")
    parser.add_argument('-set_config', action='store', metavar=('name', 'value'), nargs=2, help="Updates the user config with the corresponding key value pairs")

    try:
        args = parser.parse_args()
    except argparse.ArgumentError:
        parser.print_help()
        return

    # load the environment variables
    load_dotenv()
    
    if args.command == "execute":
        if args.prompt and args.type:
            prompt = " ".join(args.prompt)
            apitype = args.type[0].lower()
            if "rest" in apitype:
                restful_callback(prompt, args.generate_mode)
            elif "db" in apitype:
                db_callback(prompt, args.generate_mode)
            elif "fs" in apitype:
                fs_callback(prompt, args.generate_mode)
            else:
                print("Error: invalid execution type. The execution types Gorilla-x currently support are: \n" +
                      " 1. RESTful (rest)\n" +
                      " 2. Database (db)\n" +
                      " 3. Filesystem (fs)")
            return
        else:
            print("execute requires -prompt and -type to be provided")
            return
    
    if args.authorize:
        authorize_callback(args.authorize)
    elif args.remove_creds:
        remove_creds_callback(args.remove_creds)
    elif args.list_creds:
        list_callback()
    elif args.insert_creds:
        key = args.insert_creds[0]
        path = args.insert_creds[1]
        insert_callback(key, path)
    elif args.set_config:
        key = args.set_config[0]
        value = args.set_config[1]
        if key.lower() == 'max_attempt':
            if not value.isnumeric():
                print("Please enter a positive integer.")
                return
            else:
                value = int(value)
                key = 'max_attempt'
        elif key.lower() == 'model':
            if value.isdigit():
                print("Please enter a valid model version.")
            else:
                value = value.lower()
                key = "model"
        
        update_user_config(key, value)
    else:
        exit_with_help_message(parser)


if __name__ == "__main__":
    main()
