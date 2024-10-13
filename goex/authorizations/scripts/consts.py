import os
from pathlib import Path

AUTH_URL = "https://goex-services.gorilla-llm.com/authorize"
# AUTH_URL = "http://localhost:443/authorize"
CERT_FILE_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), "localhost.pem")
KEY_FILE_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), "localhost-key.pem")