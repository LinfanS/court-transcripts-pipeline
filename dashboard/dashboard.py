import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
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


def get_courts(conn: connection) -> list[str]:
    """
    Retrieves a list of courts from the database
    """

    query = """
            SELECT court_name FROM court;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return [row["court_name"] for row in result]


def get_tags(conn: connection) -> list[str]:
    """
    Retrieves a list of tags from the database
    """

    query = """
            SELECT tag_name FROM tag;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return [row["tag_name"] for row in result]


def get_verdicts(conn: connection) -> list[str]:
    """
    Retrieves a list of verdicts from the database
    """

    query = """
            SELECT verdict FROM verdict;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return [row["verdict"] for row in result]


def get_cases(conn: connection) -> list[str]:
    """
    Retrieves cases
    """

    query = """
            SELECT * FROM court_case;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def tabs():
    load_dotenv()
    conn = get_connection()
    cases, insights = st.tabs(["Cases", "Insights"])

    with cases:
        cases_df = get_cases(conn)
        st.dataframe(cases_df, use_container_width=True)

    with insights:
        with st.sidebar:

            filter = st.selectbox(
                "Filter by:", ("Judge", "Tag", "Court name", "Verdict")
            )
        judges = get_judges(conn)
        courts = get_courts(conn)
        tags = get_tags(conn)
        verdicts = get_verdicts(conn)
        col1, col2 = st.columns([0.7, 1])

        with col1:
            st.markdown(f"<div style='padding-top: 35px;'>Displaying analytics for <span style='color: red;'>{
                        filter}</span>:</div>", unsafe_allow_html=True)

        with col2:
            if filter == "Judge":
                selected_judge = st.selectbox("", judges)
            if filter == "Court name":
                selected_court = st.selectbox("", courts)
            if filter == "Tag":
                selected_court = st.multiselect("", tags)
            if filter == "Verdict":
                selected_court = st.selectbox("", verdicts)


if __name__ == "__main__":
    tabs()
