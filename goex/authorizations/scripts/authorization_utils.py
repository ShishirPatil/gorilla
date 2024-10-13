
import os
from pathlib import Path
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, os.path.dirname(parentdir))

from exec_engine.credentials.credentials_utils import CREDS_FOLDER_PATH, insert_creds

AUTHORIZATION_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)))

def authorize_service(name: str):
    name = name.lower()
    authorization_file = "{name}_authorization.py".format(name = name)
    authorization_path = os.path.join(AUTHORIZATION_FOLDER_PATH, authorization_file)

    if not os.path.exists(authorization_path):
        return False
    else:
        print(exec(open(authorization_path).read(), globals()))
        insert_creds(name, os.path.join(CREDS_FOLDER_PATH, name), target = CREDS_FOLDER_PATH, cred_type="path")
        return True
