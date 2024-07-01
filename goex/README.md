# 🦍 GoEx

| [**Website**](https://goex.gorilla-llm.com/index) |

GoEx provides a new way to interact with your favorite APIs! Powered by LLMs, GoEx executes generated code, taking into consideration any credentials you may need to access APIs. Execution security is ensured by creating reverse calls that undo any unwanted effects. Ask GoEx for anything!

## Contents <!-- omit from toc -->

- [Install](#install)
- [CLI Usage](#cli-usage)
  - [RESTful API](#restful-api)
  - [Database](#database)
  - [Filesystem](#filesystem)
- [Credentials \& Authorization Token](#credentials--authorization-token)

## Install

**1.)** Navigate inside the goex folder and set up a clean environment with **Conda** or **Python venv**

```sh
python3 -m venv goex-env
source goex-env/bin/activate
```

OR

```sh
conda create --name goex python=3.10 -y
conda activate goex
```

**2.)** Install the `goex` CLI tool

```sh
pip install -e .
```

**3.)** Install and initialize Mkcert to support OAuth2 token exchange [required for services that require https for redirect URL e.g Slack]

**Mac**

```sh
brew install mkcert
mkcert -install
mkcert localhost
```

**Linux**

Refer to the official [**Mkcert Linux Installation Instructions**](https://github.com/FiloSottile/mkcert?tab=readme-ov-file#linux)

**Windows**

```sh
choco install mkcert
mkcert -install
mkcert localhost
```

Mkcert creates a local certificate authority, enabling Gorilla to establish secure communication for OAuth2 token exchange between localhost and interacting services. The command may prompt the user to pass in their password.

**4.)** Install [**Docker**](https://docs.docker.com/engine/install/). Docker is necessary for Goex to execute LLM-generated code in a sandboxed environment. Executions via the CLI will not be successful without Docker running locally.

- At this point you should have Docker running in the background

## CLI Usage

List all commands Gorilla currently supports and their usage:

```sh
goex -h
```

Make sure to export your OpenAI API key as an environment variable.

```sh
export OPENAI_API_KEY=your_key
```

### RESTful API

Give authorizations and perform OAuth2 token exchanges with services Gorilla currently support.

```sh
goex -authorize <service> # gmail, slack, spotify, github, dropbox
```

After a service is authorized, user will be able to interact with it by providing a prompt.

```sh
# example 1
# please first run goex -authorize slack
goex execute -prompt send a funny joke to the user with email gorilla@yahoo.com on slack -type rest
```

```sh
# example 2
# this action needs user to authorize gmail
goex execute -prompt who are the senders of the 5 latest emails in my gmail inbox -type rest
```

**[Beta]** User can also specify `-generate_mode function_in_context` to generate API calls with function calling. Functions are stored in the **functions** folder, and it currently only supports a limited number of Slack features.

```sh
#example 3 (function calling)
goex execute -prompt add a smile emoji to the latest message sent to channel <CHANNEL_ID> on slack -type rest -generate_mode function_in_context
```

List all commands Gorilla current supports and their usages

### Database

To test out database interactions locally, each database server requires its own setup

#### SQLite

- If you need to create a new SQLite DB, do the following:

  ```
  sqlite3 ./goex_demo.db
  ```

  Then after, you will need to use the sqlite CLI:

  ```
  sqlite> .database
  ```

  Press `Ctrl-D` to exit out and now your `.db` file will be created!

- Run `demo/env_setup.py` to get your environment variables set up
  Use default values if you are running just the demo.

  ```
  python3 demo/env_setup.py
  ```

- Set GoEx to use SQLite for DB operations
  ```
  goex -set_config dbtype sqlite
  ```

#### Try it out!

After setting up your SQL database, you can try the following examples!

```
goex execute -prompt "Create a new table for storing user information called users, with each user having a current balance column denoting their bank balance" -type db
```

```
goex execute -prompt "Add 3 example users to the users table" -type db
```

```
goex execute -prompt "In the users table, add 500 to everyone's current balance" -type db
```

#### MySQL

- Install MySQL Server

  - For non-Mac, [install server here](https://dev.mysql.com/downloads/mysql/)
    - **Make sure to add `mysql` to path!**
  - Mac:

  ```
  brew install mysql
  ```

- Put the user, password, host, and database name info into `.env` by running this script

  ```
  python3 demo/env_setup.py
  ```

- If you don't have your own server, import the example database using `demo/mysql_setup.py` by running:

  ```sh
  python3 demo/mysql_setup.py testdb
  ```

- Set GoEx to use MySQL for DB operations
  ```
  goex -set_config dbtype mysql
  ```

### Filesystem

The goex command will be executed at the path pointed to by `fs_path` in `user_config.json`. If `fs_path` is not specified or is equal to `""`, execution will occur in the user's current working directory. Below is an example of how to set this up.

Make sure to have Git LFS installed on your machine!

Mac: `brew install git-lfs`
Windows/Linux: git-lfs.com and download

#### Try it out!

Let's first create a testing folder.

```
mkdir test
goex -set_config fs_path test
```

##### Create a Simple File

```
goex execute -prompt "Write a witty LLM joke into joke.txt" -type fs
```

##### Code Writing

You can tell Gorilla-Ex to write code for you, and directly have it be written onto your chosen directory!

```
goex execute -prompt "Write a Python program that is a calculator into a file called calculator.py" -type fs
```

## Credentials & Authorization Token

There are two types of credentials the user can add to the execution engine.

1.) [**OAuth 2.0**](https://oauth.net/2/)

Gorilla-ex follows the standard OAuth 2.0 token exchanges flow. Running the command below will redirect the user to the browser, where they will be prompted to grant permissions to Gorilla for a specific set of scopes.

```sh
goex -authorize <gmail,slack,spotify,github,dropbox>
```

After Gorilla-ex receives the token for a service, it will automatically be able to recognize the keyword in future prompts, enabling the user to perform actions on that particular platform. Additionally, the token will not be exposed to the LLM and will only be visible during execution.

We continually seek to expand our support for additional services. The authorization logic for each service resides in the authorization/scripts folder. We warmly welcome interested contributors to submit a pull request introducing a new authorization flow. **Your contributions are highly appreciated 🚀**

2.) **Raw API Key**

If the user wants to add services not supported by OAuth2, they can do so by calling the function below with `service` and `key` as parameters:

```sh
goex -insert_creds alpha_vantage {API_KEY}
```

The key will be stored in Gorilla-ex's secret store and passed on to the LLM during prompting.
