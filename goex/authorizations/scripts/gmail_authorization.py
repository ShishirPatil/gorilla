from google_auth_oauthlib.flow import InstalledAppFlow, _WSGIRequestHandler, _RedirectWSGIApp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
import os
from pathlib import Path
import pickle
import re
import requests
import ssl
import webbrowser
import wsgiref.simple_server
import wsgiref.util
from urllib.parse import quote, urlparse, parse_qs
from .consts import AUTH_URL, CERT_FILE_PATH, KEY_FILE_PATH

# If modifying SCOPES, delete the token.pickle file
SCOPES = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/calendar.readonly", 
            "openid", 
            "https://www.googleapis.com/auth/gmail.compose" ,
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.readonly",
        ]

GMAIL_FOLDER_PATH = os.path.join(os.path.dirname(Path(__file__).parent.parent), "exec_engine/credentials/gmail")
TOKEN_FILE = os.path.join(GMAIL_FOLDER_PATH, 'token.pickle')

def main():
    creds = run_gmail_flow()
    # Save the credentials for the next run
    if not os.path.isdir(GMAIL_FOLDER_PATH):
        os.mkdir(GMAIL_FOLDER_PATH)
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)

def run_gmail_flow():
        host="localhost"
        bind_addr=None
        port=8000
        authorization_prompt_message= "Please visit the link below to authorize: \n{url}"
        success_message="authorization success, you may close the window"
        open_browser=True,
        redirect_uri_trailing_slash=True
        timeout_seconds=None
        browser=None
 
        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            bind_addr or host, port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.check_hostname = False # If set to True, only the hostname that matches the certificate will be accepted
        sslctx.load_cert_chain(certfile=CERT_FILE_PATH, keyfile=KEY_FILE_PATH)

        local_server.socket = ssl.wrap_socket (local_server.socket,
            keyfile=KEY_FILE_PATH,
            certfile=CERT_FILE_PATH, server_side=True)

        redirect_uri_format = (
            "https://{}:{}/" if redirect_uri_trailing_slash else "https://{}:{}"
        )
        redirect_uri = redirect_uri_format.format(host, local_server.server_port)
        client_id = "486890796116-hfaa730qdb18ndhjs1aj195drjh5iple.apps.googleusercontent.com"
        scopes_url = "+".join([quote(x) for x in SCOPES])
        auth_url =f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&redirect_uri={quote(redirect_uri)}&scope={scopes_url}&access_type=offline"

        if open_browser:
            # if browser is None it defaults to default browser
            webbrowser.get(browser).open(auth_url, new=1, autoraise=True)

        if authorization_prompt_message:
            print(authorization_prompt_message.format(url=auth_url))
        local_server.timeout = timeout_seconds
        local_server.handle_request()
        # Note: using https here because oauthlib is very picky that
        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        code = parse_qs(urlparse(authorization_response).query)['code'][0]
        local_server.server_close()
        server_url = AUTH_URL
        data = {
            "service": "gmail-cli",
            "code": code,
            "redirect_uri": redirect_uri
        }
        r = requests.post(server_url, headers={}, json=data)
        print(r.json())
        return Credentials.from_authorized_user_info(r.json())

main()




