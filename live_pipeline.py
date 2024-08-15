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


def read_from_json(client: client) -> dict:
    """Retrieves record of cases already processed from json file on S3."""
    client.download_file(BUCKET_NAME, FILE_NAME, FILE_NAME)
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        log_json = json.load(f)
    return log_json


def handler(event: dict, context) -> None:
    count = 0
    log_json = read_from_json(get_client())
    log = list(log_json.values())[0]
    log_date = list(log_json.keys())[0]
    day, month, year = log_date.split("-")
    LIVE_URL = f"""https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=50&order=date&query=&from_date_0={day}&from_date_1={month}&from_date_2={year}&to_date_0=&to_date_1=&to_date_2=&court=uksc&court=ukpc&court=ewca%2Fciv&court=ewca%2Fcrim&court=ewhc%2Fadmin&court=ewhc%2Fadmlty&court=ewhc%2Fch&court=ewhc%2Fcomm&court=ewhc%2Ffam&court=ewhc%2Fipec&court=ewhc%2Fkb&court=ewhc%2Fmercantile&court=ewhc%2Fpat&court=ewhc%2Fscco&court=ewhc%2Ftcc&party=&judge=&page="""

    max_page_num = get_max_page_num(LIVE_URL)
    for page_num in range(1, max_page_num + 1):
        gpt_response = []
        data = get_listing_data(LIVE_URL, page_num, log)
        count += len(data)
        for index, _ in enumerate(data):
            gpt_response.append(get_data(data, index))
        table_data = assemble_data(gpt_response)
        conn = get_connection()
        insert_to_database(conn, table_data)
        log += [d.get("citation") for d in data]

        print(f"Page {page_num} inserted to database, {count} records in total")
        print(log)

    if datetime.datetime.strptime(log_date, "%d-%m-%Y").date() < datetime.date.today():
        log_date = datetime.date.today().strftime("%d-%m-%Y")
        log = []
        json_dict = {log_date: log}

    else:
        json_dict = {log_date: log}

    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(json_dict, f)
    tmp_path = "/tmp/" + FILE_NAME
    client.upload_file(tmp_path, BUCKET_NAME, FILE_NAME)
    return "Data inserted to database"


if __name__ == "__main__":
    print(handler({}, None))
