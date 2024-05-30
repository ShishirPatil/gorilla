import argparse
import os
from composer.utils import maybe_create_object_store_from_uri, parse_uri

BASE_S3_DIR = "s3://something-something-datasets/username/tooluse/gorilla"


def get_local_and_cloud_paths(local_dir, upload_dir):
    """Traverse all files in results_dir and get their paths locally.
    Create the same path in the cloud."""

    local_paths, cloud_paths = [], []
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            local_paths.append(local_path)

            local_path_relative_to_results_dir = local_path.replace(local_dir, "")
            if local_path_relative_to_results_dir[0] == "/":
                local_path_relative_to_results_dir = local_path_relative_to_results_dir[1:]
            cloud_path = os.path.join(upload_dir, local_path_relative_to_results_dir)
            cloud_paths.append(cloud_path)

    return local_paths, cloud_paths


# NOTE: this doesn't need to be an s3_dir. it works with oci too
def upload_dir(local_dir, s3_dir):

    # Get object store
    print(f"Locating cloud directory: {s3_dir}", end="\t")
    _, _, cloud_dir = parse_uri(s3_dir)
    object_store = maybe_create_object_store_from_uri(s3_dir)
    if object_store is None:
        return None
    print("Done.")

    # Get all paths
    local_paths, cloud_paths = get_local_and_cloud_paths(local_dir, cloud_dir)

    # Upload all objects to the cloud_dir
    print(f"Uploading files to {cloud_dir}", end="\t")
    for local_path, cloud_path in zip(local_paths, cloud_paths):
        object_store.upload_object(cloud_path, local_path)
    print("Done.")

    print(f"Uploaded {len(local_paths)} files from {local_dir} to {s3_dir}.")
    return s3_dir

def download_dir(local_dir, s3_dir):

    # # must have either run_name or s3_dir not be `None`
    # # if both are given, s3_dir takes priority
    # assert run_name is not None or s3_dir is not None
    # if s3_dir is None:
    #     s3_dir = os.path.join(BASE_S3_DIR, run_name)

    # Get object store
    print(f"Locating cloud directory: {s3_dir}", end="\t")
    _, _, cloud_dir = parse_uri(s3_dir)
    object_store = maybe_create_object_store_from_uri(s3_dir)
    if object_store is None:
        return None
    print("Done.")

    # Download all objects in the cloud_dir
    print(f"Downloading files to {local_dir}", end="\t")
    cloud_paths = object_store.list_objects(cloud_dir)
    for cloud_path in cloud_paths:

        path_relative_to_cloud_dir = cloud_path.replace(cloud_dir, "")
        if path_relative_to_cloud_dir[0] == "/":
            path_relative_to_cloud_dir = path_relative_to_cloud_dir[1:]
        local_path = os.path.join(local_dir, path_relative_to_cloud_dir)

        object_store.download_object(cloud_path, local_path, overwrite=True)
    print("Done.")

    print(f"Downloaded {len(cloud_paths)} files from {s3_dir} to {local_dir}.")
    return local_dir



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local_dir", type=str)
    parser.add_argument("--cloud_dir", type=str)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    upload_dir(args.local_dir, args.cloud_dir)


if __name__ == "__main__":
    main()