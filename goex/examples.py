"This file lists some popular examples on how to use Gorilla Execution Engine"



"""
PythonAPIExecutor
    - Create a python command in attempt to perform actions for the given prompt
    - If key(s) are needed, make sure they are in secret_store.json 
"""
import os
from exec_engine.db_manager import MySQLManager, SQLiteManager
from main import ExecutionEngine, PythonAPIExecutor
from exec_engine.utils import SQL_Type, RESTful_Type, Filesystem_Type
from pathlib import Path

from dotenv import load_dotenv

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)))

def mysql_insert_new_row_with_dry_run(api_call=None):
    load_dotenv()
    # DB tests
    mysql_config = {
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME')
    }
    if not api_call or not neg_api_call:
        api_call = "INSERT INTO students (name, year, major) VALUES ('Roy Huang', 4, 'Computer Science');"
        neg_api_call = """DELETE FROM students WHERE id IN (
                SELECT * FROM (
                    SELECT MAX(id) FROM students
                ) AS subquery
            );
            """
    check_call = "SELECT * FROM students;"
    
    engine = ExecutionEngine()
    engine.set_dry_run(SQL_Type, True)

    db_manager = MySQLManager(mysql_config, docker_sandbox=engine.docker_sandbox)
    db_manager.connect()
    engine.initialize_db(debug_manager=db_manager)

    # avoid dry running the SELECTs
    print("DB before the insertion")
    print(engine._exec_sql_call(check_call))
    engine.exec_api_call(api_call=api_call, debug_neg=neg_api_call, api_type=SQL_Type)
    print("DB after the insertion")
    print(engine._exec_sql_call(check_call))
    engine._exec_sql_call(neg_api_call)
    print("DB after the reversion")
    print(engine._exec_sql_call(check_call))

def create_new_file():
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    engine = ExecutionEngine()
    engine.initialize_fs(debug_path=test_dir)
    # Example usage
    engine.exec_api_call('ls -a', Filesystem_Type)
    engine.exec_api_call('echo "Hello, World!" > hello.txt', Filesystem_Type)
    engine.exec_api_call('ls -a', Filesystem_Type)
    engine.exec_api_call('cat hello.txt', Filesystem_Type)

def prompt_api_execute(prompt):
    engine = ExecutionEngine()
    engine.api_executor = PythonAPIExecutor(engine.docker_sandbox)
    creds, services = engine.api_executor.prepare_credentials(prompt)
    forward_call, backward_call = engine.gen_api_pair(prompt, api_type=RESTful_Type, credentials=creds, model="gpt-4-turbo-preview")
    print(forward_call)
    output = engine.api_executor.execute_api_call(forward_call, services)
    return output

def send_slack_message(content, display_name):
    prompt = """
    Send the message ({content}) to @{display_name} on slack .
    """.format(content=content, display_name=display_name.replace(" ", ""))

    print(prompt_api_execute(prompt))

def delete_slack_message(display_name):
    prompt = """
    Delete the latest message I sent to the user {display_name} on slack direct message.
    """.format(display_name=display_name.replace(" ", "")).lower()

    print(prompt_api_execute(prompt))

def latest_n_emails_gmail(n):
    prompt = """
    Who are the senders of the {n} most recent email in my gmail inbox?
    """.format(n=n)

    print(prompt_api_execute(prompt))

def ask_general_question(question):
    print(prompt_api_execute(question))

"""
FS management system
"""
def full_file_system_demo():
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    engine = ExecutionEngine(path=test_dir)
    engine.initialize_fs(debug_path=test_dir)
    # Example usage
    engine._exec_filesystem_call('ls -a')
    engine.exec_api_call('echo "Hello, World!" > hello.txt', Filesystem_Type)
    engine._exec_filesystem_call('ls -a')
    engine._exec_filesystem_call('cat hello.txt')

    engine.commit_api_call(Filesystem_Type)
    print('\n\nCommited!\n\n')

    engine.exec_api_call('echo "Bad File!" > not_good.txt', Filesystem_Type)
    engine._exec_filesystem_call('ls -a', Filesystem_Type)
    engine._exec_filesystem_call('cat not_good.txt', Filesystem_Type)


    engine.undo_api_call(Filesystem_Type)
    print('\n\nReverted!\n\n')

    engine.exec_api_call('ls -a', Filesystem_Type)


def mysql_insert_new_row_no_dry_run(api_call=None):
    load_dotenv()
    # DB tests
    mysql_config = {
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME')
    }
    if not api_call or not neg_api_call:
        api_call = "INSERT INTO students (name, year, major) VALUES ('Roy Huang', 4, 'Computer Science');"
        neg_api_call = """
            DELETE FROM students WHERE id IN (
                SELECT * FROM (
                    SELECT MAX(id) FROM students
                ) AS subquery
            );
            """
    check_call = "SELECT * FROM students;"

    engine = ExecutionEngine()
    db_manager = MySQLManager(mysql_config, docker_sandbox=engine.docker_sandbox)
    db_manager.connect()
    engine.initialize_db(debug_manager=db_manager)

    print('Current State:')
    print(engine._exec_sql_call(check_call))

    engine.exec_api_call("INSERT INTO students (name, year, major) VALUES ('Ray Huang', 4, 'Computer Science');", api_type=SQL_Type)

    print('New Commited State:')
    print(engine._exec_sql_call(check_call))

    engine.commit_api_call(SQL_Type)

    engine.exec_api_call("INSERT INTO students (name, year, major) VALUES ('Wrong dude', 1, 'high schooler');", api_type=SQL_Type)

    print('Uncommited Changed State:')
    print(engine._exec_sql_call(check_call))

    engine.undo_api_call(SQL_Type)

    print('Previous Commited Changed State:')
    print(engine._exec_sql_call(check_call))

def fs_all_in():
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    engine = ExecutionEngine()
    engine.initialize_fs(debug_path=test_dir)
    # Example usage
    engine.exec_api_call('ls -a')
    engine.exec_api_call('echo "Hello, World!" > hello.txt')
    engine.exec_api_call('ls -a')
    engine.exec_api_call('cat hello.txt')

    engine.commit_api_call(Filesystem_Type)
    print('\n\nCommited!\n\n')

    engine.exec_api_call('echo "Bad File!" > not_good.txt')
    engine.exec_api_call('ls -a')
    engine.exec_api_call('cat not_good.txt')

    engine.undo_api_call(SQL_Type)
    print('\n\nReverted!\n\n')

    engine.exec_api_call('ls -a')

def mysql_end_to_end_insert():
    load_dotenv()
    # DB tests
    mysql_config = {
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME')
    }

    check_call = "SELECT * FROM students;"

    engine = ExecutionEngine()
    engine.set_dry_run(SQL_Type, True)

    db_manager = MySQLManager(mysql_config, docker_sandbox=engine.docker_sandbox)
    db_manager.connect()
    engine.initialize_db(debug_manager=db_manager)

    prompt = "i want to insert a new student name Shishir Patil who's a 1st year and a computer science major into the students table"
    # prompt = "i want to delete a student named ray Doe in the students table"

    print("Before execution:")
    print(engine._exec_sql_call(check_call))

    engine.run_prompt(prompt, SQL_Type)

    print("After execution:")
    print(engine._exec_sql_call(check_call))

def sqlite_insert_with_dry_run_llm_reversion():
    engine = ExecutionEngine()

    db_path = os.path.join(ROOT_FOLDER_PATH, 'docker/sqllite_docker/example_sqlite.db')
    config = {'path': db_path}
    db_manager = SQLiteManager(config, engine.docker_sandbox)
    db_manager.connect()

    engine.initialize_db(debug_manager=db_manager)
    engine.set_dry_run(SQL_Type, True)
    check_call = "SELECT * FROM projects;"

    prompt = "i want to insert a new example row into the projects table"

    print("Before execution:")
    print(engine._exec_sql_call(check_call))

    engine.run_prompt(prompt, SQL_Type)

    print("After execution:")
    print(engine._exec_sql_call(check_call))

    engine.undo_api_call(SQL_Type)

def fs_joke_prompt_demo():
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    engine = ExecutionEngine(path=test_dir)
    engine.initialize_fs(debug_path=test_dir)
    engine.set_dry_run(Filesystem_Type, True)
    # Example usage

    print("Before execution:")
    print(engine._exec_filesystem_call('ls -a'))

    engine.run_prompt("I want to create a file named joke.txt with a witty joke inside", Filesystem_Type)
    engine.commit_api_call(Filesystem_Type)

    print("After execution:")
    print(engine._exec_filesystem_call('ls -a'))
    print(engine._exec_filesystem_call('cat joke.txt'))



if __name__ == "__main__":

    """
    NOTE: Feel free to uncomment any of the tests below to run the demo

    IMPORTANT: Follow the README to get set up
    """

    """
    File System Examples
    
    You can see the actual file changes inside test/ directory
    """
    # full_file_system_demo()
    # create_new_file()
    # fs_joke_prompt_demo()

    """
    MySQL Examples
    """
    # mysql_insert_new_row_with_dry_run()
    # mysql_insert_new_row_no_dry_run()
    # mysql_end_to_end_insert()

    """
    sqllite Examples
    """
    # sqlite_insert_with_dry_run_llm_reversion()

    """
    RESTful Examples
    """
    # SLACK (requires OAuth)
    # send_slack_message("yo", "Shishir Patil")
    # delete_slack_message("Shishir Patil")
    
    # SPOTIFY (requires OAuth)
    # spotify is sometimes a bit spotty (heh) and does not always work
    # create a new file in my dropbox account with some jokes
    # ask_general_question("find the user info associated with my spotify account")

    # DROPBOX (requires OAuth)
    # ask_general_question("create a new file in my dropbox account with some jokes")
    # ask_general_question("list all files in my dropbox account")

    # STRIPE (requires API key)
    # ask_general_question("create a new customer with email aaronhao@berkeley.edu on stripe")
    # ask_general_question("add 300 dollars to the balance of the customer with email aaronhao@berkeley.edu on stripe")

    # GITHUB (requires oauth)
    # ask_general_question("get my profile information from github")
    # ask_general_question("raise a github issue for my repository at [REPO] with text: [TEXT]")

    # DISCORD (requires oauth)
    # ask_general_question("what is the email associated with my discord account")

    # ask_general_question("What's the top rising stock today on alphavantage?")
    # ask_general_question("What's the weather today in San Francisco?")
    # ask_general_question("What's the estimated time of arrival to the Salesforce tower Sanfrancisco if I leave berkeley right now with Bart")
    pass
