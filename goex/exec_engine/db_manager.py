from exec_engine.docker_sandbox import DockerSandbox

"""
    This module will handle all database interactions
    The DBManager class is the base class for all database managers
"""

class DBManager:
    """Base class for all DB connectors.

    Attributes:
        connection_config (type): JSON Config for connection.

    Methods:
        connect: Establish connections to the DB
        execute_db_call: Execute DB call
        commit_db_calls: Commit DB calls
        rollback_db_calls: Rollback DB calls
        close: Close the connection to the database

    """

    def __init__(self, connection_config):
        """Initialize the DBManager.
        
        Args:
            connection_config (dict): Configuration for connecting to the database. This can be a path for file-based databases or connection details for server-based databases.

        """
        self.connection_config = connection_config
        self.docker_sandbox = None

    def connect(self):
        """Establish connection to the database."""
        raise NotImplementedError
    
    def get_schema_as_string(self):
        prompt = ""
        for table_name, schema in self.schema.items():
            prompt += f"Table '{table_name}':\n"
            for column in schema:
                column_name, column_type, is_nullable, key, default, extra = column
                prompt += f"- Column '{column_name}' of type '{column_type}'"
                if is_nullable == 'NO':
                    prompt += ", not nullable"
                if key == 'PRI':
                    prompt += ", primary key"
                prompt += "\n"
            prompt += "\n"
        return prompt
    
    def task_to_prompt(self, task_description, forward=True):
        """Format the schemas of all tables into a prompt for GPT, including a task description."""
        prompt = ""

        if self.schema == None:
            raise Exception("Please connect to the database first.")
        
        if self.schema:
            "No schema information available."
            prompt += "Given the following table schemas in a sqlite database:\n\n"
            prompt += self.get_schema_as_string()
        
        if forward:
            prompt += f"Task: {task_description}\n\n"
            prompt += "Based on the task, select the most appropriate table and generate an SQL command to complete the task. In the output, only include SQL code."
        else:
            prompt += f"SQL command: {task_description}\n\n"
            prompt += "Based on the SQL command and the given table schemas, generate a reverse command to reverse the SQL command. In the output, only include SQL code."
        return prompt

    def execute_db_call(self, call):
        """Execute DB call.
        
        Args:
            call (str): DB call to execute.
        """
        raise NotImplementedError
    
    def fetch_db_call(self, call):
        raise NotImplementedError
    
    def commit_db_calls(self):
        """Commit DB calls."""
        raise NotImplementedError
    
    def rollback_db_calls(self):
        """Rollback DB calls not committed"""
        raise NotImplementedError

    def close(self):
        """Close the connection to the database."""
        raise NotImplementedError


class SQLiteManager(DBManager):
    """SQLite database manager.
    
    Attributes:
        _sqlite_imported (bool): flag to check if sqlite3 is imported.
        
    Methods:
        connect: Establish connections to the DB
        execute_db_call: Execute SQL call
        commit_db_calls: Commit SQL calls
        rollback_db_calls: Rollback SQL calls
        close: Close the connection to the database
    """
    _sqlite_imported = False  # flag to check if sqlite3 is imported
    db_type = "sqlite"
    TEST_CONFIG = "" # No config required to access sqlite
    def __init__(self, connection_config, docker_sandbox: DockerSandbox = None):
        """Initialize the SQLLiteManager.

        Args:
            connection_config(str): path to the database file.
        """
        if not SQLiteManager._sqlite_imported:
            global sqlite3
            import sqlite3
            SQLiteManager._sqlite_imported = True
        keys = connection_config.keys()

        if any(key not in keys for key in ['path']):
            raise ValueError("Failed to initialize SQLite Manager due to bad configs")

        self.db_path = connection_config['path']
        if not self.db_path:
            raise ValueError("Failed to initialize SQLite Manager due to missing path")

    def update_schema_info(self):
        schema_info = {}
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        for (table_name,) in tables:
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            schema_info[table_name] = self.cursor.fetchall()
        
        self.schema = schema_info

    def connect(self):
        """Establish connection to the SQLLite3 database and create a cursor."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.update_schema_info()
        
    
    def execute_db_call(self, call):
        if not self.conn:
            self.connect()
        try:
            commands_list = [cmd.strip() for cmd in call.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            for command in commands_list:
                if command.upper().startswith('SELECT'):
                    self.cursor.execute(command)
                    print(self.cursor.fetchall())
                else:
                    self.cursor.execute(command)
            self.update_schema_info()
            return 0
        except Exception as e:
            return 1

    
    def fetch_db_call(self, call):
        if not self.conn:
            self.connect()
        try:
            self.cursor.execute(call)
            ret_val = self.cursor.fetchall()
            self.update_schema_info()
            return ret_val
        except Exception as e:
            return []

    def commit_db_calls(self):
        """Commit SQL calls."""
        if not self.conn:
            self.connect()
        self.conn.commit()

    def rollback_db_calls(self):
        """Rollback SQL calls not committed"""
        if not self.conn:
            self.connect()
        self.conn.rollback()
        self.close()
        self.connect()

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()


class MySQLManager(DBManager):
    """MySQL database manager.
    
    Attributes:
        _mysql_imported (bool): flag to check if pymysql is imported.
        
    Methods:
        connect: Establish connections to the DB
        execute_db_call: Execute SQL call
        commit_db_calls: Commit SQL calls
        rollback_db_calls: Rollback SQL calls
        close: Close the connection to the database
    """
    _mysql_imported = False
    db_type = "mysql"
    TEST_CONFIG = "{'host': '127.0.0.1', 'user': 'root', 'password': ''}\n Use Pymysql and make sure to create the database using subprocess before connection."
    def __init__(self, connection_config, docker_sandbox: DockerSandbox = None):
        """Initialize the MySQLManager.

        Args:
            connection_config (dict): configuration for the database connection, including keys for 'user', 'password', 'host', and 'database'.
        """
        if not MySQLManager._mysql_imported:
            global pymysql
            import pymysql
            MySQLManager._mysql_imported = True
        
        keys = connection_config.keys()

        if any(key not in keys for key in ['host', 'user', 'password', 'database']):
            raise ValueError("Failed to initialize MySQL Manager due to bad configs")
        elif any([not connection_config['host'], not connection_config['user'], not connection_config['password'], not connection_config['database']]):
            raise ValueError("Failed to initialize MySQL Manager due to missing configs")

        self.connection_config = {
            'host': connection_config['host'],
            'user': connection_config['user'],
            'password': connection_config['password'],
            'database': connection_config['database'],
            "client_flag": pymysql.constants.CLIENT.MULTI_STATEMENTS
        }

    def connect(self):
        """Establish connection to the MySQL database and create a cursor."""
        self.conn = pymysql.connect(**self.connection_config)
        self.cursor = self.conn.cursor()
        self.update_schema_info()

    def update_schema_info(self):
        schema_info = {}
        
        self.cursor.execute("SHOW TABLES")
        tables = self.cursor.fetchall()
        for (table_name,) in tables:
            self.cursor.execute(f"DESCRIBE {table_name}")
            schema_info[table_name] = self.cursor.fetchall()
        
        self.schema = schema_info
    
    def execute_db_call(self, call):
        """Execute a SQL call using the cursor."""
        if not self.conn:
            self.connect()
        try:
            self.cursor.execute(call)
            self.update_schema_info()
            return 0
        except Exception as e:
            return 1

    def fetch_db_call(self, call: str) -> list[dict]:
        """Execute a SQL call and return the results.
        
        Args:
            call (str): SQL query to execute.
        
        Returns:
            list[dict]: A list of dictionaries representing each row in the query result.
        """
        if not self.conn:
            self.connect()
        try:
            self.cursor.execute(call)
            ret_val = self.cursor.fetchall()
            self.update_schema_info()
            return ret_val
        except Exception as e:
            return []

    def commit_db_calls(self):
        """Commit SQL calls."""
        if not self.conn:
            self.connect()
        self.conn.commit()

    def rollback_db_calls(self):
        """Rollback SQL calls not committed."""
        if not self.conn:
            self.connect()
        self.conn.rollback()

    def close(self):
        """Close the cursor and the connection to the database."""
        if self.conn:
            self.cursor.close()
            self.conn.close()
