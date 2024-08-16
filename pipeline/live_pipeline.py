"""Python script to run the live pipeline on AWS Lambda to add new court cases to the database"""

from os import getenv
import json
from datetime import datetime, date
import boto3
from botocore import client
from extract import get_listing_data, get_max_page_num
from transform import get_data, assemble_data
from load import get_connection, insert_to_database

FILE_NAME = "log.json"
BUCKET_NAME = "c12-court-transcripts"


def get_client() -> client:
    """Initiates a connection to the S3 AWS Cloud using required credentials."""
    aws_client = boto3.client(
        "s3",
        aws_access_key_id=getenv("ACCESS_KEY_ID"),
        aws_secret_access_key=getenv("SECRET_ACCESS_KEY"),
    )
    return aws_client


def read_from_json(aws_client: client) -> dict:
    """Retrieves record of cases already processed from json file on S3."""
    aws_client.download_file(BUCKET_NAME, FILE_NAME, FILE_NAME)
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        log_json = json.load(f)
    return log_json


def extract_log_and_date(log_json: dict) -> tuple[str, list]:
    """Retrieve the key and value from dictionary"""
    log_date, log = log_json.popitem()
    return log_date, log


def construct_live_url(log_date: str) -> str:
    """Constructs the URL to scrape based on the log date"""
    day, month, year = log_date.split("-")
    return f"""https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=50&order=date&query=&from_date_0={day}&from_date_1={month}&from_date_2={year}&to_date_0=&to_date_1=&to_date_2=&court=uksc&court=ukpc&court=ewca%2Fciv&court=ewca%2Fcrim&court=ewhc%2Fadmin&court=ewhc%2Fadmlty&court=ewhc%2Fch&court=ewhc%2Fcomm&court=ewhc%2Ffam&court=ewhc%2Fipec&court=ewhc%2Fkb&court=ewhc%2Fmercantile&court=ewhc%2Fpat&court=ewhc%2Fscco&court=ewhc%2Ftcc&party=&judge=&page="""


def process_pages(live_url: str, max_page_num: int, log: list) -> None:
    """Processes all pages of the live URL to extract and insert data into the database"""
    count = 0
    for page_num in range(1, max_page_num + 1):
        gpt_response = []
        data = get_listing_data(live_url, page_num, log)
        count += len(data)
        for index, _ in enumerate(data):
            gpt_response.append(get_data(data, index))
        table_data = assemble_data(gpt_response)
        conn = get_connection()
        insert_to_database(conn, table_data)
        log += [d.get("citation") for d in data]
        print(f"Page {page_num} inserted to database, {count} records in total")


def update_log_date_and_log(log_date: str, log: list) -> tuple[str, list]:
    """Updates the log date and log list"""
    if datetime.strptime(log_date, "%d-%m-%Y").date() < date.today():
        log_date = date.today().strftime("%d-%m-%Y")
        log = []
    return log_date, log


def save_log_to_file(log_date: str, log: list) -> None:
    """Saves the log to a json file"""
    json_dict = {log_date: log}
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(json_dict, f)


def upload_log_to_s3(aws_client: client) -> None:
    """Uploads the log file to S3"""
    # tmp_path = "/tmp/" + FILE_NAME  # for lambda
    tmp_path = FILE_NAME  # for local
    aws_client.upload_file(tmp_path, BUCKET_NAME, FILE_NAME)


def handler(event: dict, context) -> None:
    """Main function to run the live pipeline on AWS Lambda"""
    aws_client = get_client()
    log_json = read_from_json(aws_client)
    log_date, log = extract_log_and_date(log_json)
    live_url = construct_live_url(log_date)

    max_page_num = get_max_page_num(live_url)
    if max_page_num == 0:
        return "No new data to insert, exiting"

    process_pages(live_url, max_page_num, log)

    log_date, log = update_log_date_and_log(log_date, log)
    save_log_to_file(log_date, log)
    upload_log_to_s3(aws_client)

    return "Data inserted to database"


if __name__ == "__main__":
    print(handler({}, None))
