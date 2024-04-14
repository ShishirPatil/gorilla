"""Manages Docker containers for a controlled environment."""

import docker
import os
from pathlib import Path

from exec_engine.container_utils import container_utils as utils
from exec_engine.container_utils.code_parser import extract_dependencies
from exec_engine.credentials.credentials_utils import get_cred_paths, CREDS_FOLDER_PATH

from exec_engine.utils import format_container_logs, RESTful_Type, SQL_Type, Filesystem_Type

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent)
DOCKER_FOLDER_PATH = os.path.join(ROOT_FOLDER_PATH, "docker/docker")
DOCKER_REQUIREMENTS_PATH = os.path.join(DOCKER_FOLDER_PATH, "requirements.txt")
DOCKERFILE_PATH = os.path.join(DOCKER_FOLDER_PATH, "dockerfile")
DOCKER_EXECUTION_PATH = os.path.join(DOCKER_FOLDER_PATH, "python_executor.py")

MYSQL_DOCKER_FOLDER_PATH = os.path.join(ROOT_FOLDER_PATH, "docker/mysql_docker")
MYSQL_DOCKER_REQUIREMENTS_PATH = os.path.join(MYSQL_DOCKER_FOLDER_PATH, "requirements.txt")
MYSQL_DOCKERFILE_PATH = os.path.join(MYSQL_DOCKER_FOLDER_PATH, "dockerfile")
MYSQL_DOCKER_EXECUTION_PATH = os.path.join(MYSQL_DOCKER_FOLDER_PATH, "python_executor.py")

def get_docker_paths(docker_folder_path):
    requirements_path = os.path.join(docker_folder_path, "requirements.txt")
    dockerfile_path = os.path.join(docker_folder_path, "dockerfile")
    execution_path = os.path.join(docker_folder_path, "python_executor.py")
    
    return requirements_path, dockerfile_path, execution_path

class DockerSandbox:
    def __init__(self, client_config = {}):
        self.client = None
        self.auto_save_image = True
        self.auto_remove = True

        if not client_config:
            try:
                self.client = docker.from_env()
            except Exception as e:
                print("Error: {error}.\nIf you haven't already, please install Docker https://docs.docker.com/get-docker/".format(error=e))
        else:
            try:
                self.client = docker.DockerClient(**client_config)
            except Exception as e:
                print("Unable to initialize a docker client based on client_config {client_config}. Encountered an error with message {error}".format(client_config=client_config, error=e))


    def create_sandbox(self):
        # Create a new Docker container with a basic image
        return self.client.containers.run("ubuntu", detach=True)
    

    def create_python_sandbox(self, code, image_id, credentials=None, attached_volume = None):
        volumes = []

        if credentials:
            paths, not_found = get_cred_paths(credentials, CREDS_FOLDER_PATH)
            for service in paths:
                host_path = paths[service]
                container_path = "/sandbox/credentials/" + service
                volumes.append(host_path + ":" + container_path)

        else:
            volumes = {
                # path on your machine/host
                os.path.abspath("credentials"): {
                    "bind": "/sandbox/credentials",  # path inside the container
                    "mode": "rw",
                }
            }
            if attached_volume:
                volumes[attached_volume] = {
                    "bind": "/sandbox/test_dir",
                    "mode": "ro",
                }

        try:
            container = self.client.containers.run(
                image_id,
                command = 
                    ['python',  'python_executor.py',  'code_execute'],
                environment = {
                    "CODE": code
                },
                volumes=volumes,
                stderr = True,
                stdout=True,
                detach=True,
            )
            container.wait()
            docker_out, docker_debug = format_container_logs(container)
            if self.auto_remove:
                container.remove()

        except Exception as e:
            print("Failure occured inside client.containers.run with the following error message:", e)
            return None
        
        return {"output": docker_out, "debug": docker_debug}

    def create_image_from_code(self, code, api_type=RESTful_Type):
        if api_type == SQL_Type:
            docker_folder_path = MYSQL_DOCKER_FOLDER_PATH
        else:
            docker_folder_path = DOCKER_FOLDER_PATH

        requirements_path, dockerfile_path, execution_path = get_docker_paths(docker_folder_path)
        try:
            extract_dependencies(code, path=requirements_path)
            image_hash = utils.get_files_hash(dockerfile_path, requirements_path, execution_path)
            image_id = utils.find_local_docker_image(image_hash)
        except Exception as e:
            print("ERROR:, ", e)
            return

        # Run the container using the image specified if exists, else pull the image from docker hub
        try:
            if image_id:
                self.client.images.get(image_id)
        except Exception as e:
            try:
                # Use the low-level API to stream the pull response
                low_level_client = docker.APIClient()
                low_level_client.pull(image_id, stream=True, decode=True)
                self.client.images.get(image_id)
            except:
                image_id = None
            
        try:
            if not image_id:
                image_id = self.client.images.build(path=docker_folder_path)[0].short_id
                if self.auto_save_image:
                    utils.save_image_hash(image_hash, image_id)
        except Exception as e:
            print("Unable to build docker image, returned with error: {error}".format(error=e))
            return None
        
        return image_id

    def delete_sandbox(self, container):
        container.stop()
        container.remove()
