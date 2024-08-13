import requests
from bs4 import BeautifulSoup, element
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor, execute_values
from os import getenv
from dotenv import load_dotenv


def get_connection() -> connection:
    """
    Establishes a connection to the database
    """
    return psycopg2.connect(
        host=getenv("DB_HOST"),
        user=getenv("DB_USER"),
        password=getenv("DB_PASSWORD"),
        database=getenv("DB_NAME"),
        port=getenv("DB_PORT")
    )


def get_judge_rows(url: str) -> element:
    whole_page = requests.get(url)
    soup = BeautifulSoup(whole_page.content, 'html.parser')
    table_contents = soup.find('div', class_="page__content [ flow ]")
    rows = table_contents.find_all("td")
    return rows


def get_bench_judges(url: str) -> list[tuple]:
    return [(item.get_text(),) for index, item in enumerate(get_judge_rows(url)) if index % 2 == 1 and item.get_text() != "Name" and item.get_text()[0].isalpha()]


def get_district_judges_magistrates(url: str) -> list[tuple]:
    return [(item.get_text(),) for index, item in enumerate(get_judge_rows(url)) if index % 3 == 0 and item.get_text() != "Judge"]


def get_diversity_high_court_judges(url: str) -> list[tuple]:
    return [(item.get_text(),) for index, item in enumerate(get_judge_rows(url)) if index % 2 == 0 and item.get_text() != "Name" and item.get_text()[0].isalpha()]


def get_judge_advocates(url: str) -> list[tuple]:
    return [(item.get_text(),) for index, item in enumerate(get_judge_rows(url)) if index % 2 == 0 and item.get_text() != "Judge"]


def get_circuit_district_judges(url: str) -> list[tuple]:
    rows = get_judge_rows(url)
    names = []
    for index, item in enumerate(rows):
        if index % 3 == 0 and item.get_text() != "Judge":
            name = item.get_text()
            if not item.get_text()[-1].isalpha():
                name = name[:-1]
            names.append((name,))
    return names


def gather_all_judges() -> list[tuple]:
    high_court_masters = get_diversity_high_court_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/hc-masters-list/")

    bench_chairs = get_bench_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/bench-chairmen-list/")

    district_judges_magistrates = get_district_judges_magistrates(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/dj-mags-ct-list/")

    diversity_community_judges = get_diversity_high_court_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/diversity-and-community-relations-judges-list/")

    judge_advocates_general = get_judge_advocates(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/jag-list/")

    circuit_judges = get_circuit_district_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/circuit-judge-list/")

    district_judges = get_circuit_district_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/district-judge-list/")

    diversity_community_magistrates = get_diversity_high_court_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/diversity-community-and-relations-magistrates/")

    return high_court_masters + bench_chairs + district_judges_magistrates + diversity_community_judges + judge_advocates_general + circuit_judges + district_judges + diversity_community_magistrates


def upload_judges(conn: connection, judges: list[tuple]) -> None:
    query = """
            INSERT INTO judge(judge_name)
            VALUES %s
            ON CONFLICT DO NOTHING
            ;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        execute_values(curs, query, judges)
        conn.commit()


if __name__ == "__main__":
    load_dotenv()
    db_conn = get_connection()
    judges = gather_all_judges()
    upload_judges(db_conn, judges)
