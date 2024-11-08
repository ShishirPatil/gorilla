"""
Setup script for postgresql
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
        print("Usage: python3 postgresql_setup.py database_name")
        sys.exit(1)

    ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent)

    postgresql_username = os.environ.get('DATABASE_USER')
    postgresql_password = os.environ.get('DATABASE_PASSWORD')
    database_name = sys.argv[1]
    dump_file_path = os.path.join(ROOT_FOLDER_PATH, "docker/postgresql_docker/checkpoints/database_dump.sql")

    # Command to create the database if it doesn't exist
    create_db_command = f'echo "SELECT \'CREATE DATABASE {database_name}\' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = \'{database_name}\')\gexec" | psql'

    # Command to import the .sql file into the postgresql database
    import_command = f'psql --username={postgresql_username} {database_name} < {dump_file_path}'

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
