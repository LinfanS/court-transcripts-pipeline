"""Python script to run the batch pipeline locally to insert past 
court cases to the database and cache GPT data in Redis"""

from ast import literal_eval
import logging
import redis
from rich.progress import Progress
import nltk
from extract import get_listing_data, get_max_page_num
from transform import get_data, assemble_data
from load import get_connection, insert_to_database

nltk.download("wordnet")

# Initialize Redis connection
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

BATCH_URL = """https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=50&order=date&query=&from_date_0=1&from_date_1=1&from_date_2=2020&to_date_0=11&to_date_1=8&to_date_2=2024&court=uksc&court=ukpc&court=ewca%2Fciv&court=ewca%2Fcrim&court=ewhc%2Fadmin&court=ewhc%2Fadmlty&court=ewhc%2Fch&court=ewhc%2Fcomm&court=ewhc%2Ffam&court=ewhc%2Fipec&court=ewhc%2Fkb&court=ewhc%2Fmercantile&court=ewhc%2Fpat&court=ewhc%2Fscco&court=ewhc%2Ftcc&party=&judge=&page="""


def initialise_logger() -> logging.Logger:
    """Initialise the logger to log to both file and console."""
    logger = logging.getLogger("batch_pipeline")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler("batch_pipeline.log")
    console_handler = logging.StreamHandler()
    file_handler.setLevel(logging.INFO)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def main() -> None:
    """Main function to process all pages of the batch URL and insert data into the database"""
    logger = initialise_logger()
    max_page_num = get_max_page_num(BATCH_URL)
    if max_page_num == 0:
        message = "No new data to insert, exiting"
        logger.info(message)
        return None

    count = 0
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing batch data...", total=max_page_num)
        for page_num in range(1, max_page_num + 1):
            data = get_listing_data(BATCH_URL, page_num)
            count += len(data)
            gpt_response = []

            for index, item in enumerate(data):
                court_case_citation = item.get("citation")
                if r.exists(court_case_citation):
                    case_details = literal_eval(
                        r.hgetall(court_case_citation)["case_details"]
                    )
                    gpt_response.append(case_details)
                    message = (
                        f"Cache hit for {court_case_citation}, retrieved from Redis."
                    )
                else:
                    response = get_data(data, index)
                    r.hset(
                        court_case_citation,
                        mapping={"case_details": str(response)},
                    )
                    gpt_response.append(response)
                    message = (
                        f"Cache miss for {court_case_citation}, "
                        "GPT data fetched and stored in Redis."
                    )
                logger.info(message)

            insert_to_database(get_connection(), assemble_data(gpt_response))
            message = f"Page {page_num} inserted to database, {count} records in total"
            logger.info(message)
            progress.update(task, advance=1)

    logger.info("Batch data successfully inserted to database")
    return None


if __name__ == "__main__":
    main()
