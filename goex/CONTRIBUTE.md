# Contributing to the Repo

## Adding a new database

Adding a new database will require the following to be added:

1. A new Manager subclass (like the DBManager classes in `exec_engine/db_manager.py`)
   1. Needs to include logic for supporting transactional commits/rollbacks regardless of the database type (Ensure reversibility for all database types)
   2. Implementation should be similar to ` MySQLManager` or `SQLiteManager`
   3. Be able to format a user prompt with additional database specific info (like schema) to inform the LLM how to generate an accurate API call.
2. \[Optional\] If dry-running is wanted:
   1. Add a new folder inside `docker/` much like `docker/mysql_docker`
   2. Make sure the dockerfile sets up the environment for the database deployment
   3. Create a copy of the database and copy it to the docker container
   4. Create a reversibility script for dry-running like `exec_engine/db_reversion_test.txt`
      1. This script is written in txt since it will be passed into the docker environment and run with `python_executor.py`
