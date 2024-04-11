"""To speed up build runtimes. Previously used docker images are cached in images.json so that they could be reused"""

import hashlib
import os
import json
from pathlib import Path

ROOT_FOLDER_PATH = os.path.dirname(Path(os.path.realpath(__file__)).parent.parent)
IMAGES_FILE_PATH = os.path.join(ROOT_FOLDER_PATH, "docker/misc/images.json")

def get_files_hash(*file_paths):
    """Return the SHA256 hash of multiple files."""
    hasher = hashlib.sha256()
    for file_path in file_paths:
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
    return hasher.hexdigest()

def find_local_docker_image(image_hash):
    hash_file_path = IMAGES_FILE_PATH
    if not os.path.exists(hash_file_path):
        return None
    with open(hash_file_path, "r") as f:
        stored_hashes = json.load(f)
    if image_hash in stored_hashes:
        return stored_hashes[image_hash]
    else:
        return None
    
def save_image_hash(image_hash, image_name):
    hash_file_path = IMAGES_FILE_PATH
    try:
        if not os.path.exists(hash_file_path):
            with open(hash_file_path, "w") as f:
                stored_hashes = {}
                stored_hashes[image_hash] = image_name
                json.dump(stored_hashes, f)
            return True
        else:
            stored_hashes = {}
            with open(hash_file_path, "r") as f:
                stored_hashes = json.load(f)
            with open(hash_file_path, "w") as f:
                stored_hashes[image_hash] = image_name
                json.dump(stored_hashes, f)
            return True
    except Exception as e:
        print(e)
        return False

