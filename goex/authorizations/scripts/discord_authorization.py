from google_auth_oauthlib.flow import InstalledAppFlow, _WSGIRequestHandler, _RedirectWSGIApp
from google.auth.transport.requests import Request
import os
from pathlib import Path
import pickle
import re
import requests
import ssl
import webbrowser
import wsgiref.simple_server
import wsgiref.util
from urllib.parse import quote

DISCORD_FOLDER_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), 'exec_engine/credentials/discord')
CREDENTIAL_FILE = os.path.join(os.path.dirname(Path(__file__).parent), "credentials/discord_credentials.json")
TOKEN_FILE = os.path.join(DISCORD_FOLDER_PATH, 'token.pickle')

CERT_FILE_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), "localhost.pem")
KEY_FILE_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), "localhost-key.pem")

def main():
    creds = None
    # Check if token.pickle file exists and is valid
    flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIAL_FILE, [])

    creds = run_discord_flow(flow)
    # Save the credentials for the next run
    if not os.path.isdir(DISCORD_FOLDER_PATH):
        os.mkdir(DISCORD_FOLDER_PATH)
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)

def run_discord_flow(flow: InstalledAppFlow):
        host="localhost"
        bind_addr=None
        port=8000
        authorization_prompt_message=flow._DEFAULT_AUTH_PROMPT_MESSAGE
        success_message=flow._DEFAULT_WEB_SUCCESS_MESSAGE
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
        auth_url, _ = flow.authorization_url()

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
        print(authorization_response)
        response_regex = r".*code=(.*)&state=(.*)"
        print(re.findall(response_regex, authorization_response))
        code = re.findall(response_regex, authorization_response)[0]

        local_server.server_close()

        data = {"grant_type":"authorization_code", "code": code, "redirect_uri":redirect_uri}

        url = "https://discord.com/api/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(url, 
                          data=data, 
                          headers=headers,
                          auth=("1214447388354420736", "Io25U2nXzMDE6GgtfBqmVWbLPhv7LuoG"))

        print(r.json())
        return r.json()['access_token']

main()
