"""Python script to initialise a JSON file and send it to an S3 bucket."""

import json
from os import getenv
import boto3
from botocore import client


BUCKET_NAME = "c12-court-transcripts"


def get_client() -> client:
    """Initiates a connection to the S3 AWS Cloud using required credentials."""
    aws_client = boto3.client(
        "s3",
        aws_access_key_id=getenv("ACCESS_KEY_ID"),
        aws_secret_access_key=getenv("SECRET_ACCESS_KEY"),
    )
    return aws_client


def initialise_json(live_start_date: str) -> None:
    """Initialises a JSON file, writes the live pipeline start date and sends it to S3"""
    log_json = {live_start_date: []}
    file_name = "log.json"

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(log_json, f)
    get_client().upload_file(file_name, BUCKET_NAME, file_name)
    print("Initialised JSON file and sent to S3")


if __name__ == "__main__":
    initialise_json("12-08-2024")
