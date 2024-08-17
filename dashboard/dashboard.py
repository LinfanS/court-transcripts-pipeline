import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from os import getenv
from dotenv import load_dotenv

st.set_page_config(layout="wide")


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
            SELECT j.judge_name
            FROM judge_assignment as ja
            JOIN judge as j on j.judge_id = ja.judge_id
            ;
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
            SELECT c.court_name 
            FROM court as c
            JOIN court_case as cc ON c.court_id = cc.court_id
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    courts = []
    for row in result:
        if row['court_name'] not in courts:
            courts.append(row['court_name'])

    return courts


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


def get_case_titles(conn: connection) -> list[str]:
    """
    Retrieves a list of case titles from the database
    """

    query = """
            SELECT title FROM court_case;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return [row["title"] for row in result]


def get_cases_info_for_case(conn: connection, title: str) -> dict:
    """
    Retrieves information that we want to display for each case
    """

    query = """
            SELECT cc.court_case_id, cc.summary, v.verdict, cc.title, cc.court_date, cc.case_url, c.court_name, cc.verdict_summary
            FROM court_case as cc
            JOIN court as c ON c.court_id = cc.court_id
            JOIN verdict as v ON v.verdict_id = cc.verdict_id
            WHERE cc.title = %s
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()
    return result[0]


def get_judges_for_case(conn: connection, title: str) -> list[str]:
    """
    Retrieves judge/judges that we want to display for each case
    """

    query = """
            SELECT j.judge_name
            FROM judge_assignment as ja
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN court_case as cc ON ja.court_case_id = cc.court_case_id
            WHERE cc.title = %s
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()
    return [row["judge_name"] for row in result]


def get_tags_for_case(conn: connection, title: str) -> list[str]:
    """
    Retrieves a list of tags from the database for a specific case
    """

    query = """
            SELECT t.tag_name 
            FROM tag_assignment as ta
            JOIN tag as t ON t.tag_id = ta.tag_id
            JOIN court_case as cc ON cc.court_case_id = ta.court_case_id
            WHERE cc.title = %s;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()

    return [row["tag_name"] for row in result]


def get_participants_and_lawyers_for_case(conn: connection, title: str, is_defendant: bool) -> list[dict]:
    """
    Retrieves a list of prosecutors from the database for a specific case
    """

    query = """
            SELECT p.participant_name, l.lawyer_name, lf.law_firm_name, cc.title
            FROM participant_assignment as pa
            JOIN participant as p ON p.participant_id = pa.participant_id
            JOIN court_case as cc ON cc.court_case_id = pa.court_case_id
            JOIN lawyer as l ON l.lawyer_id = pa.lawyer_id
            JOIN law_firm as lf ON lf.law_firm_id = l.law_firm_id
            WHERE cc.title = %s 
            AND pa.is_defendant = %s
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title, is_defendant))
        result = curs.fetchall()

    return result


def format_participants_to_string(participants: list[dict], is_defendant: bool) -> str:
    person = "Claimant"
    lawyer_type = ""
    if is_defendant:
        person = "Defendant"
        lawyer_type = ""
    html = ""
    current_participants = []
    for row in participants:
        participant = row.get("participant_name").title()
        if participant in current_participants:
            continue
        if participant:
            current_participants.append(participant)
        law_firm = row.get("law_firm_name")
        lawyer = row.get("lawyer_name")
        html += f"<div>{person}: {participant}"
        if lawyer and lawyer != 'None':
            html += f".<br> Represented by {lawyer_type}: {lawyer.title()}"
        if law_firm and law_firm != 'None':
            html += f" from {law_firm} <br> <br>"
        html += "</div>"
    return html

def display_claimants_and_defendants(selected_case):            
    col1, col2 = st.columns(2)
    with col1:
        claimants = st.toggle("Display claimants and their Lawyers")
    with col2:
        defendants = st.toggle("Display defendants and their Lawyers")
    if claimants:
        prosecuting_participants = get_participants_and_lawyers_for_case(
            conn, selected_case, False)
        prosecuting_participants_html = format_participants_to_string(
            prosecuting_participants, False)
        st.markdown(prosecuting_participants_html,
                    unsafe_allow_html=True)
    if defendants:
        defending_participants = get_participants_and_lawyers_for_case(
            conn, selected_case, True)
        defending_participants_html = format_participants_to_string(
            defending_participants, True)
        st.markdown(defending_participants_html,
                    unsafe_allow_html=True)
        
def format_case_presentation(conn: connection, title: str) -> str:
    case_specific_info = get_cases_info_for_case(conn, title)
    judges = get_judges_for_case(conn, title)
    tags = get_tags_for_case(conn, title)
    judges_str = ""
    for judge in judges:
        judges_str += judge + ", "
    tags_str = ""
    valid_tags = []
    for tag in tags:
        if tag in valid_tags:
            continue
        valid_tags.append(tag.lower())
        tags_str += tag.lower() + ", "
    col1, col2, col3 = st.columns([3,3,2])
    with col1:
        st.markdown(f"""**Case ID:** [{case_specific_info['court_case_id']}]({
                    case_specific_info['case_url']})""", help = "Click here to view the original file")
    with col2:
        st.markdown(f"**Verdict:** <span style='color: red;'><strong><u>{case_specific_info['verdict']}</u></strong>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Date:** ")
    st.markdown(f"<h3><span style='color:white'><u>{case_specific_info["title"]}</u></span></h3>", unsafe_allow_html=True)
    st.html(f"<u>Court:</u> {case_specific_info['court_name']}")
    st.html(f"<u>Judge/s:</u> {judges_str[:-2]}")
    st.html(f"<u>Tags:</u> {tags_str[:-2]}")
    st.html(f"<u>Verdict summary:</u> {case_specific_info['verdict_summary']}")
    st.html(f"<u>Summary:</u> {case_specific_info["summary"]}")
    display_claimants_and_defendants(case_specific_info['title'])
    
    # header = f"""
    #             <h3>Case Title: {case_specific_info["title"]}</h3>
    #             <h4>Case id: {case_specific_info["court_case_id"]} | Court date: {case_specific_info["court_date"]}</h4>
    #             <h4>Court Name: {case_specific_info['court_name']}</h4>
    #             <h4>Judge/s: {judges_str[:-2]}</h4>
    #             <h4>Tags: {tags_str[:-2]}</h4>
    #             <div>Summary: {case_specific_info["summary"]}</div>
    #             <h4>Verdict: <span style='color: red;'>{case_specific_info["verdict"]}</span></h4>
    #             <div> Verdict summary: {case_specific_info['verdict_summary']}</div>
    #             <div style='margin-bottom: 50px;'></div>
    #         """
    # return header


def get_judge_chart_data_verdict(conn: connection):
    """
    Retrieves judge case data required for verdict chart
    """

    query = """
            SELECT COUNT(cc.court_case_id), v.verdict, j.judge_name
            FROM court_case as cc
            JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN verdict as v ON v.verdict_id = cc.verdict_id
            
            GROUP BY v.verdict, j.judge_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_judge_chart_data_tag(conn: connection):
    """
    Retrieves judge case data required for tag chart
    """

    query = """
            SELECT COUNT(cc.court_case_id), t.tag_name, j.judge_name
            FROM court_case as cc
            JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN tag_assignment as ta ON ta.court_case_id = cc.court_case_id
            JOIN tag as t ON t.tag_id = ta.tag_id
            
            GROUP BY t.tag_name, j.judge_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_judge_data_court_type(conn: connection):
    """
    Retrieves judge case data required for cases over time
    """

    query = """
            SELECT COUNT(cc.court_case_id), c.court_name, j.judge_name
            FROM court_case as cc
            JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN court as c ON c.court_id = cc.court_id
            GROUP BY c.court_name, j.judge_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_court_data_verdict(conn: connection):
    """
    Retrieves court_name data for verdicts
    """

    query = """
            SELECT COUNT(cc.court_case_id), v.verdict, c.court_name
            FROM court_case as cc
            JOIN verdict as v ON v.verdict_id = cc.verdict_id
            JOIN court as c ON c.court_id = cc.court_id
            GROUP BY v.verdict, c.court_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_court_data_tags(conn: connection):
    """
    Retrieves court_name data for tags
    """

    query = """
            SELECT COUNT(cc.court_case_id), t.tag_name, c.court_name
            FROM court_case as cc
            JOIN tag_assignment as ta ON ta.court_case_id = cc.court_case_id
            JOIN tag as t ON t.tag_id = ta.tag_id
            JOIN court as c ON c.court_id = cc.court_id
            GROUP BY t.tag_name, c.court_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_court_data_judges(conn: connection):
    """
    Retrieves court_name data for judges
    """

    query = """
            SELECT COUNT(cc.court_case_id), j.judge_name, c.court_name
            FROM court_case as cc
            JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN court as c ON c.court_id = cc.court_id
            GROUP BY j.judge_name, c.court_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()

    return pd.DataFrame(result)


def get_tag_data_verdict(conn: connection):
    """
    Retrieves tag data for verdicts
    """

    query = """
            SELECT COUNT(cc.court_case_id), v.verdict, t.tag_name
            FROM court_case as cc
            JOIN verdict as v ON v.verdict_id = cc.verdict_id
            JOIN tag_assignment as ta ON ta.court_case_id = cc.court_case_id
            JOIN tag as t ON t.tag_id = ta.tag_id
            GROUP BY v.verdict, t.tag_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_tag_data_judges(conn: connection):
    """
    Retrieves tag data for judges
    """

    query = """
            SELECT COUNT(cc.court_case_id), j.judge_name, t.tag_name
            FROM court_case as cc
            JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
            JOIN judge as j ON j.judge_id = ja.judge_id
            JOIN tag_assignment as ta ON ta.court_case_id = cc.court_case_id
            JOIN tag as t ON t.tag_id = ta.tag_id
            GROUP BY j.judge_name, t.tag_name
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_cases_over_time(conn: connection):
    """
    Retrieves cases over time
    """

    query = """
            SELECT extract(month FROM court_date) as month, COUNT(*) as case_count
            FROM court_case as cc
            GROUP BY month 
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_cases_over_time_per_court(conn: connection):
    """
    Retrieves cases over time
    """

    query = """
            SELECT cc.court_date, c.court_name, COUNT(*) as case_count
            FROM court_case as cc
            JOIN court as c ON c.court_id = cc.court_id
            GROUP BY cc.court_date, c.court_name 
            ;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def plot_filter_pie(df: pd.DataFrame, selected_filter: str, filter: str, tab: str):
    filtered_data = df[df[tab] == selected_filter]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count:Q'),
        color=alt.Color(field=filter, type='nominal'),
        tooltip=[filter, 'count']
    ).properties(
        title=f"{filter.capitalize()} Distribution for {selected_filter}"
    )
    return pie_chart


def plot_pie(df: pd.DataFrame, filter: str):
    aggregated_data = df.groupby(filter).sum().reset_index()
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count:Q'),
        color=alt.Color(field=filter, type='nominal'),
        tooltip=[filter, 'count']
    ).properties(
        title=f"{filter.capitalize()} Distribution"
    )
    return pie_chart


def plot_filter_pie_tags(df: pd.DataFrame, selected_filter: list[str], filter: str, tab: str):
    filtered_data = df[df[tab].isin(selected_filter)]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    print(aggregated_data)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        alt.Theta('count:Q').stack(True),
        color=alt.Color(field=filter, type='nominal'),
        tooltip=[filter, 'count']
    )
    return pie_chart


def plot_cases_over_months(df: pd.DataFrame):
    return alt.Chart(df.reset_index()).mark_line().encode(
        x='month:T',
        y='case_count:Q').interactive()


def plot_cases_over_months_per_court(df: pd.DataFrame):
    return alt.Chart(df.reset_index()).mark_line().encode(
        x='court_date:T',
        y='case_count:Q',
        color='court_name:N').interactive()


def tabs():
    load_dotenv()
    conn = get_connection()
    cases, insights, filtered_insights = st.tabs(
        ["Cases", "General Insights", "Filtered Insights"])

    with cases:
        available_cases = get_case_titles(conn)
        st.markdown("<h4>Court case summary: </h4>", unsafe_allow_html=True)
        selected_case = st.selectbox("Court case summary: ", sorted(available_cases),
                                     placeholder='Select a case to be displayed', index=None,
                                     label_visibility="collapsed")
        if selected_case:
            html = format_case_presentation(conn, selected_case)
            st.markdown(html, unsafe_allow_html=True)



    with insights:
        col1, col2 = st.columns(2)
        with col1:
            verdict_df = get_judge_chart_data_verdict(conn)
            st.write(plot_pie(verdict_df, 'verdict'))
            court_df = get_judge_data_court_type(conn)
            st.write(plot_pie(court_df, 'court_name'))
        with col2:
            tag_df = get_judge_chart_data_tag(conn)
            st.write(plot_pie(tag_df, 'tag_name'))
        
            case_count_df = get_cases_over_time(conn)
            st.altair_chart(plot_cases_over_months(case_count_df))
            court_cases_over_time_df = get_cases_over_time_per_court(conn)
            st.altair_chart(plot_cases_over_months_per_court(
            court_cases_over_time_df))

    with filtered_insights:
        with st.sidebar:

            filter = st.selectbox(
                "Filter by:", ("Judge", "Tag", "Court name")
            )
        judges = get_judges(conn)
        courts = get_courts(conn)
        tags = get_tags(conn)
        col1, col2 = st.columns([0.7, 1])

        with col1:
            st.markdown(f"""<div style='padding-top: 35px;'>Displaying analytics for <span style='color: red;'>{
                        filter}</span>:</div>""", unsafe_allow_html=True)

        with col2:
            if filter == "Judge":
                selected_judge = st.selectbox("Select a judge", judges, label_visibility="hidden")
            if filter == "Court name":
                selected_court = st.selectbox("Select a court", courts, label_visibility="hidden")
            if filter == "Tag":
                st.markdown("""<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""",unsafe_allow_html=True,)
                selected_tags = st.multiselect("Select a tag", tags, label_visibility="hidden")

        if filter == "Judge":
            judge_verdict_df = get_judge_chart_data_verdict(conn)
            st.write(plot_filter_pie(judge_verdict_df,
                     selected_judge, 'verdict', 'judge_name'))
            judge_tag_df = get_judge_chart_data_tag(conn)
            st.write(plot_filter_pie(judge_tag_df,
                     selected_judge, 'tag_name', 'judge_name'))
            judge_court_df = get_judge_data_court_type(conn)
            st.write(plot_filter_pie(judge_court_df,
                     selected_judge, 'court_name', 'judge_name'))

        if filter == "Court name":
            court_verdict_df = get_court_data_verdict(conn)
            st.write(plot_filter_pie(court_verdict_df,
                     selected_court, 'verdict', 'court_name'))
            court_tag_df = get_court_data_tags(conn)
            st.write(plot_filter_pie(court_tag_df,
                     selected_court, 'tag_name', 'court_name'))
            court_judge_df = get_court_data_judges(conn)
            st.write(plot_filter_pie(court_judge_df,
                     selected_court, 'judge_name', 'court_name'))

        if filter == "Tag":
            if selected_tags:
                title = "<h3>Insights for: "
                for tag in selected_tags:
                    title += tag + ", "
                st.markdown(f"{title[:-2]}</h4>", unsafe_allow_html=True)
                tag_verdict_df = get_tag_data_verdict(conn)
                st.altair_chart(plot_filter_pie_tags(tag_verdict_df,
                                                     selected_tags, 'verdict', 'tag_name'))
                tag_judge_df = get_tag_data_judges(conn)
                st.altair_chart(plot_filter_pie_tags(
                    tag_judge_df, selected_tags, 'judge_name', 'tag_name'))


def display():
    st.title('Court Transcripts :judge:')
    tabs()


if __name__ == "__main__":
    conn = get_connection()
    display()
    # case = get_cases_info_for_case(conn, "MTA v The Lord Chancellor")
    # print(case)
    # judges = get_judges_for_case(conn, "MTA v The Lord Chancellor")
    # tags = get_tags_for_case(conn, "MTA v The Lord Chancellor")
    # participants = get_participants_and_lawyers_for_case(
    #     conn, "XS1 (A Child Proceeding by her Mother and Litigation Friend XS2) v West Hertfordshire Hospitals NHS Trust", True)
    # print(participants)
