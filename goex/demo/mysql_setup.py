"""
Setup script for MySQL
"""

import subprocess
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Check if the database name was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python3 mysql_setup.py database_name")
        sys.exit(1)

    ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent)

    mysql_username = os.environ.get('DATABASE_USER')
    mysql_password = os.environ.get('DATABASE_PASSWORD')
    database_name = sys.argv[1]
    dump_file_path = os.path.join(ROOT_FOLDER_PATH, "docker/mysql_docker/checkpoints/database_dump.sql")

    # Command to create the database if it doesn't exist
    create_db_command = f'mysql -u{mysql_username} -p{mysql_password} -e "CREATE DATABASE IF NOT EXISTS {database_name};"'

    # Command to import the .sql file into the MySQL database
    import_command = f'mysql -u{mysql_username} -p{mysql_password} {database_name} < {dump_file_path}'

    # Execute the create database command
    try:
        subprocess.run(create_db_command, shell=True, check=True)
        print(f"Database '{database_name}' created (if it didn't already exist).")
    except subprocess.CalledProcessError as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

    # Execute the import command
    try:
        subprocess.run(import_command, shell=True, check=True)
        print("Import successful")
    except subprocess.CalledProcessError as e:
        print(f"Error during import: {e}")
