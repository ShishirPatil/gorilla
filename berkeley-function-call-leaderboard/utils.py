import os
from pathlib import Path

import boto3


def get_s3_client():
    s3 = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", ""),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    )
    return s3


def upload_to_s3(local_filepath, s3_location):
    try:
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "")
        s3 = get_s3_client()
        s3.upload_file(local_filepath, bucket_name, s3_location)
        print(f"Uploaded {local_filepath} to s3://{bucket_name}/{s3_location}")
    except Exception as e:
        print(
            f"Error uploading file {local_filepath} to s3://{bucket_name}/{s3_location} \n {e}"
        )


def remove_from_s3(s3_location):
    try:
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "")
        s3 = get_s3_client()
        s3.delete_object(Bucket=bucket_name, Key=s3_location)
        print(f"Deleted s3://{bucket_name}/{s3_location}")
    except Exception as e:
        print(f"Error Deleting s3://{bucket_name}/{s3_location} \n {e}")


def download_from_s3(s3_location, local_filepath):
    try:
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "")
        s3 = get_s3_client()
        Path(local_filepath).parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(bucket_name, s3_location, local_filepath)
        print(f"file s3://{bucket_name}/{s3_location} downloaded to {local_filepath}")

    except Exception as e:
        print(f"Error downloading file s3://{bucket_name}/{s3_location} \n {e}")


def list_from_s3(prefix=""):
    try:
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "")
        s3 = get_s3_client()
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                print(obj["Key"])
        else:
            print("Bucket is empty or not accessible.")
        return response

    except Exception as e:
        print(f"Error listing files i  s3://{bucket_name} \n {e}")
