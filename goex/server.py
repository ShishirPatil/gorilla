# *********************************************************
# *                                                       *
# * This server is used to interface with frontend at     *
# * https://github.com/gorilla-llm/gorilla-react-frontend.*
# *                                                       *
# *********************************************************


from fastapi import FastAPI, HTTPException, Request
from main import ExecutionEngine, PythonAPIExecutor
import re
import requests
from urllib.parse import quote, urlencode
from google_auth_oauthlib.flow import InstalledAppFlow
from fastapi.middleware.cors import CORSMiddleware
import exec_engine.credentials.credentials_utils as credentials_utils
from exec_engine.utils import SQL_Type, RESTful_Type, Filesystem_Type
import json
import base64

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    # This function intercepts OPTIONS requests and returns the appropriate response
    #return {"method": "OPTIONS"}
    return {}

########## GOOGLE AUTH ################################
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.readonly", 
    "openid", 
    "https://www.googleapis.com/auth/gmail.compose" ,
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]
FRONTEND_GMAIL_CREDENTIAL_FILE = "authorizations/credentials/frontend_gmail_credentials.json"
CLI_GMAIL_CREDENTIAL_FILE = "authorizations/credentials/gmail_credentials.json"
frontend_flow = InstalledAppFlow.from_client_secrets_file(
    FRONTEND_GMAIL_CREDENTIAL_FILE, SCOPES)
frontend_flow.redirect_uri = 'postmessage'
cli_flow = InstalledAppFlow.from_client_secrets_file(
    CLI_GMAIL_CREDENTIAL_FILE, SCOPES)
########## GOOGLE AUTH END ##############################



########## CRED HELPER FUNCTIONS ######################
def getGoogleCredsFrontend(code, redirect_uri):
    frontend_flow.fetch_token(code = code)
    return json.loads(frontend_flow.credentials.to_json())
def getGoogleCredsCli(code, redirect_uri):
    cli_flow.redirect_uri = redirect_uri
    cli_flow.fetch_token(code = code)
    return json.loads(cli_flow.credentials.to_json())

SLACK_CREDENTIAL_FILE = "authorizations/credentials/slack_credentials.json"
def getSlackCreds(code, redirect_uri):
    with open(SLACK_CREDENTIAL_FILE) as json_file:
        client_data = json.load(json_file)["installed"]
    data = {"code": code, 
            "client_id": client_data["client_id"], 
            "client_secret": client_data["client_secret"],
            "redirect_uri":redirect_uri
            }
    headers = {"content-type": "application/x-www-form-urlencoded;"}
    r = requests.post("https://slack.com/api/oauth.v2.access", 
                    data=data,
                    headers=headers)
    return {'token': r.json()['authed_user']['access_token']}

DISCORD_CREDENTIAL_FILE = "authorizations/credentials/discord_credentials.json"
def getDiscordCreds(code, redirect_uri):
    with open(DISCORD_CREDENTIAL_FILE) as json_file:
        client_data = json.load(json_file)["installed"]
    data = {"grant_type":"authorization_code", "code": code, "redirect_uri":redirect_uri}
    url = "https://discord.com/api/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, 
                        data=data, 
                        headers=headers,
                        auth=(client_data['client_id'], client_data['client_secret']))
    return {'token' : r.json()['access_token']}

SPOTIFY_CREDENTIAL_FILE = "authorizations/credentials/spotify_credentials.json"
def getSpotifyCreds(code, redirect_uri):
    with open(SPOTIFY_CREDENTIAL_FILE) as json_file:
        client_data = json.load(json_file)["installed"]
    data = {"code": code, "client_id":client_data['client_id'], "grant_type": 'authorization_code', "redirect_uri": redirect_uri}
    form_body = urlencode(data)
    url = "https://accounts.spotify.com/api/token"
    headers = {"content-type": "application/x-www-form-urlencoded", "Authorization": 'Basic ' + base64.b64encode((f"{client_data['client_id']}:{client_data['client_secret']}").encode()).decode()}
    r = requests.post(url, 
                        data=form_body, 
                        headers=headers)
    return {'token' : r.json()['access_token']}

DROPBOX_CREDENTIAL_FILE = "authorizations/credentials/dropbox_credentials.json"
def getDropboxCreds(code, redirect_uri):
    with open(DROPBOX_CREDENTIAL_FILE) as json_file:
        client_data = json.load(json_file)["installed"]
    data = {"code": code, "client_id":client_data['client_id'], 'client_secret' : client_data['client_secret'],"grant_type": 'authorization_code', "redirect_uri": redirect_uri}
    form_body = urlencode(data)
    url = client_data['token_uri']
    r = requests.post(url, data=form_body)
    return {'token' : r.json()['access_token']}

GITHUB_CREDENTIAL_FILE = "authorizations/credentials/github_credentials.json"
def getGithubCreds(code, redirect_uri):
    with open(GITHUB_CREDENTIAL_FILE) as json_file:
        client_data = json.load(json_file)["installed"]
    params = {
        "code": code, 
        "client_id":client_data['client_id'],
        "client_secret" : client_data['client_secret'],
        "redirect_uri": redirect_uri
        }   
    url = client_data['token_uri']
    headers = {'Accept': 'application/json'}
    r = requests.post(url, params=params, headers=headers)
    return {'token' : r.json()['access_token']}
########## CRED HELPER FUNCTIONS END ######################




@app.post('/authorize')  # takes in temp code from google oauth and returns creds
async def authorize(request: Request):
    try:
        request_content = await request.json()
        code = request_content['code']
        service = request_content['service']
        redirect_uri = request_content['redirect_uri']
        if(service== 'gmail'):
            credentials = getGoogleCredsFrontend(code, redirect_uri)
        elif(service=='gmail-cli'):
            credentials = getGoogleCredsCli(code, redirect_uri)
        elif(service == 'slack'):
            credentials = getSlackCreds(code, redirect_uri)
        elif(service == 'discord'):
            credentials = getDiscordCreds(code, redirect_uri)
        elif(service == 'spotify'):
            credentials = getSpotifyCreds(code, redirect_uri)
        elif(service == 'dropbox'):
            credentials = getDropboxCreds(code, redirect_uri)
        elif(service == 'github'):
            credentials = getGithubCreds(code, redirect_uri)
        else:
            raise HTTPException(status_code=404, detail="Service Not Found")
        return credentials
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="unable to execute with error message {e}".format(e=e))

    



@app.post('/prompt')
async def prompt_engine(request: Request):
    print("IN PROMPT")
    try:
        request_content = await request.json()
        creds = request_content['creds'] # burden on frontend to get the right cred
        prompt = request_content['prompt']
        engine = ExecutionEngine() # should we be making a new engine for each request?
        engine.api_executor = PythonAPIExecutor(engine.docker_sandbox)
        forward_call, backward_call = engine.gen_api_pair(prompt, api_type=RESTful_Type, credentials=creds, model="gpt-4-turbo-preview")
        return {"forward_call" : forward_call, "backward_call" : backward_call}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="unable to execute with error message {e}".format(e=e))

@app.post('/execute')
async def execute(request: Request):
    try:
        request_content = await request.json()
        forward_call = request_content['code']
        #creds = request_content['creds']
        engine = ExecutionEngine() # should we be making a new engine for each request?
        engine.api_executor = PythonAPIExecutor(engine.docker_sandbox)
        output = engine.api_executor.execute_api_call(forward_call)
        print(output)
        return output
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="unable to execute with error message {e}".format(e=e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=443, log_level="debug", reload=True)
