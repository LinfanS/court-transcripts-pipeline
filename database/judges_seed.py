import requests
from bs4 import BeautifulSoup, element
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor, execute_values
from os import getenv
from dotenv import load_dotenv

COMMON_JUDGE_WORDS = ("Senior", "(Magistrates’", " His", "Master", 'King’s', "(The", "The", "King's", "Remembrancer)", "Bench", "Chief", "Chancery",
                      "Costs", "Judge", "(Chief", "Taxing", "Master)", "Insolvency", "and", "Companies", "Court", "Registrar", "District", "(MC)", "His", "Her", "Honour", "Tribunal", "Employment", "Deputy", "Magistrate)", "CBE", "DL", "(Deputy", "Lead", "DCRJ)", "Upper", "Recorder", "of", "London,", "Regional", "ICC", "(Magistrates", "(Magistrates'", "Court)", "KC", "Assistant", "Advocate", "General", "Lieutenant", "Colonel", "(Retired)", "JP", "", "OBE")


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
    """
    Gets all table rows from tables on the url given
    """
    whole_page = requests.get(url)
    soup = BeautifulSoup(whole_page.content, 'html.parser')
    table_contents = soup.find('div', class_="page__content [ flow ]")
    rows = table_contents.find_all("td")
    return rows


def get_bench_judges(url: str) -> list[str]:
    """
    Retrieves all bench judges
    """
    return [item.get_text() for index, item in enumerate(get_judge_rows(url)) if index % 2 == 1 and item.get_text() != "Name" and item.get_text()[0].isalpha()]


def get_district_judges_magistrates(url: str) -> list[str]:
    """
    Retrieves all district judge magistrates
    """
    return [item.get_text() for index, item in enumerate(get_judge_rows(url)) if index % 3 == 0 and item.get_text() != "Judge"]


def get_diversity_high_court_judges(url: str) -> list[str]:
    """
    Retrieves diversity and community judges or high court judges
    """
    return [item.get_text() for index, item in enumerate(get_judge_rows(url)) if index % 2 == 0 and item.get_text() != "Name" and item.get_text()[0].isalpha()]


def get_judge_advocates(url: str) -> list[str]:
    """
    Retrieves all judge advocates
    """
    return [item.get_text() for index, item in enumerate(get_judge_rows(url)) if index % 2 == 0 and item.get_text() != "Judge"]


def get_circuit_district_judges(url: str) -> list[str]:
    """
    Retrieves all circuit district judges
    """
    rows = get_judge_rows(url)
    names = []
    for index, item in enumerate(rows):
        if index % 3 == 0 and item.get_text() != "Judge":
            name = item.get_text()
            if not item.get_text()[-1].isalpha():
                name = name[:-1]
            names.append(name)
    return names


def gather_all_judges() -> list[str]:
    """
    Retrieves and combines all judges names
    """
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


def standardise_judge_names(judges: list[str]) -> list[tuple]:
    """
    Makes the judges names just the personal name and creates a list of tuples ready for upload
    """
    standardised_names = []
    for judge in judges:
        name_parts = judge.split(" ")
        good_parts = []
        for part in name_parts:
            if part not in COMMON_JUDGE_WORDS and part[0].isalpha():
                good_parts.append(part)
        standardised_names.append((" ".join(good_parts),))
    return standardised_names


def upload_judges(conn: connection, judges: list[tuple]) -> None:
    """
    Uploads all the judges names to the database
    """
    query = """
            INSERT INTO judge(judge_name)
            VALUES %s
            ON CONFLICT DO NOTHING
            ;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        execute_values(curs, query, standardise_judge_names(judges))
        conn.commit()


if __name__ == "__main__":
    load_dotenv()
    db_conn = get_connection()
    judges = gather_all_judges()
    # print(judges)
    # print(standardise_judge_names(judges))
    # upload_judges(db_conn, judges)
