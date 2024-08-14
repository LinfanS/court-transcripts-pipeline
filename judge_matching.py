from rapidfuzz import process, fuzz
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from os import getenv
from dotenv import load_dotenv

MATCHING_PERCENT = 95


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


def get_judges(conn: connection) -> list[str]:
    """
    Retrieves a list of judges from the database
    """

    query = """
            SELECT judge_name FROM judge;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return [row["judge_name"] for row in result]


def match_judge(judge: str, current_judges: list) -> tuple | None:
    """
    Matches the judge received from the transcript to ones from the database if possible
    """
    match = process.extractOne(
        judge, current_judges, score_cutoff=MATCHING_PERCENT, scorer=fuzz.token_set_ratio)
    if match:
        return match[0]
    return None


if __name__ == "__main__":
    load_dotenv()
    conn = get_connection()
    judges = get_judges(conn)
    match = match_judge("Judge Bond", judges)
    print(match)
