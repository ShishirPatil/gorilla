"""Common utility functions and classes"""

import os
from pathlib import Path
from typing import NewType

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent)
DEFAULT_CHECKPOINT_PATH = os.path.join(ROOT_FOLDER_PATH, 'checkpoints')

SQL_Type = NewType("SQL_Type", str)
Filesystem_Type = NewType("Filesystem_Type", str)
RESTful_Type = NewType("RESTful_Type", str)

def format_container_logs(container):
    docker_out = []
    for log in container.logs(stdout=True, stderr=False, stream=True):
        log = log.decode("utf-8")
        if log == "\n":
            continue
        else:
            if log[-1] == "\n":
                log = log[:-1]
            docker_out.append(log)
    
    docker_debug = container.logs(stdout=False, stderr=True).decode("utf-8")
    return docker_out, docker_debug
