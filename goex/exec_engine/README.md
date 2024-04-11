# Gorilla-X

## Execution Workflows

We categorize API calls into several categories, namely, RESTful API, filesystem APIs, database APIs, and POSIX APIs. A main concern we are trying to address is how to safely handle situations where LLMs may produce code that leads to unintended behaviors.

### File System

With filesystems API calls, they will be handled by an wrapper class `FSManager` that handles all the code execution as well as reversion functionalities. Upon initialization inside `ExecutionEngine`, the newly created FSManager based on either a user specified directory or the CWD will be initialized to track changes.

- Initialize a Git repo to keep track of changes
  - if it is a directory of size > 200MB, we use Git LFS

`FSManager` will handle all of the history reversion based on standard Git principles to provide a robust version control system for easy rollbacks to the pre-LLM execution state.

### Database

With Database API calls, they will be handled by a wrapper interface `DBManager` that gets implemented into specific managers for each DB type (i.e. `MySQLManager`).

The `DBManager` will handle execution of the API call, as well as keeping track of the current open transaction awaiting commit or rollback if the user decides to not perform dry run testing of the API calls (option 1).

If the user has the dry run testing option on (option 2), then before the API call gets executed locally, a docker container will be spawned with a copy of the current database you are working with (`exec_engine/utils.py`).

- the setup required for each DB will be performed in a shell script located in `docker/docker/container_setup`

Afterwards, a Python script will run with the API call wrapped around a reversion tester to see if the state before running the API call and after the API call + its negation are the same. This gets captured and sent back as the dry run result. From their, the CLI or GUI can prompt the user to confirm or cancel the operation if it is deemed to be irreversible by the generated negation API.
