"""Code to allow for a dashboard"""
import re
from os import getenv
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from notify import get_sns_client, sub_to_topics

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
            JOIN judge as j on j.judge_id = ja.judge_id;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    judges = []
    for row in result:
        if row['judge_name'] not in judges:
            judges.append(row['judge_name'])
    return judges


def get_courts(conn: connection) -> list[str]:
    """
    Retrieves a list of courts from the database
    """
    query = """
            SELECT c.court_name 
            FROM court as c
            JOIN court_case as cc ON c.court_id = cc.court_id;
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
    query = """SELECT tag_name FROM tag;"""
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return [row["tag_name"] for row in result]


def get_case_titles(conn: connection) -> list[str]:
    """
    Retrieves a list of case titles from the database
    """
    query = """SELECT title FROM court_case;"""
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
            WHERE cc.title = %s;
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
            WHERE cc.title = %s;
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
            AND pa.is_defendant = %s;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title, is_defendant))
        result = curs.fetchall()
    return result


def format_participants_to_string(participants: list[dict], is_defendant: bool) -> str:
    """
    Get all participants and format them to the desired html to then display
    """
    html = ""
    current_participants = []
    for row in participants:
        participant = row.get("participant_name").title()
        if participant not in current_participants:
            current_participants.append(participant)
        law_firm = row.get("law_firm_name")
        lawyer = row.get("lawyer_name")
        html += f"<div><strong>{participant}</strong><br>"
        if lawyer and lawyer != 'None':
            html += f"Represented by: {lawyer.title()} <br>"
        if law_firm and law_firm != 'None':
            html += f"From: {law_firm} <br>"
        html += '<br>'
        html += "</div>"
    return html


def display_claimants_and_defendants(selected_case):
    """
    Special display for  claimants and defendants so that it stands out
    """
    st.divider()
    container = st.container(border=False)
    col1, col2, col3 = container.columns([5, 1, 5])
    with col1:
        st.markdown("""<span style='color:white'>Claimants</span>""",
                    unsafe_allow_html=True)
        prosecuting_participants = get_participants_and_lawyers_for_case(
            conn, selected_case, False)
        prosecuting_participants_html = format_participants_to_string(
            prosecuting_participants, False)
        st.markdown(prosecuting_participants_html,
                    unsafe_allow_html=True)
    with col3:
        st.markdown("""<span style='color:white'>Defendants</span>""",
                    unsafe_allow_html=True)
        defending_participants = get_participants_and_lawyers_for_case(
            conn, selected_case, True)
        defending_participants_html = format_participants_to_string(
            defending_participants, True)
        st.markdown(defending_participants_html,
                    unsafe_allow_html=True)


def format_case_presentation(conn: connection, title: str) -> str:
    """
    Code used to render how and what information will be displayed of each cases
    """
    case_specific_info = get_cases_info_for_case(conn, title)
    judges = get_judges_for_case(conn, title)
    tags = get_tags_for_case(conn, title)
    judges_str = ""
    for judge in judges:
        judges_str += judge + ", "
    tags_str = ""
    valid_tags = []
    for tag in tags:
        if tag not in valid_tags:
            valid_tags.append(tag.lower())
            tags_str += tag.lower() + ", "
    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        st.markdown(f"""**Case ID:** [{case_specific_info['court_case_id']}]({
                    case_specific_info['case_url']})""", help="Click here to view the original file")
    with col2:
        st.markdown(f"""**Verdict:** <span style='color: red;'><strong><u>{
                    case_specific_info['verdict']}</u></strong>""", unsafe_allow_html=True)
    with col3:
        st.markdown(
            f"""**Date:** {case_specific_info["court_date"].strftime('%d-%m-%Y')}""")
    st.html(f"""<h3><span style='color:white'>{
        case_specific_info["title"]}</span></h3>""")
    st.html(f"""<u>Court:</u> {case_specific_info['court_name']}""")
    st.html(f"""<u>Judge/s:</u> {judges_str[:-2]}""")
    st.html(f"""<u>Tags:</u> {tags_str[:-2]}""")
    st.html(
        f"""<u>Verdict summary:</u> {case_specific_info['verdict_summary']}""")
    st.html(f"""<u>Summary:</u> {case_specific_info["summary"]}""")
    display_claimants_and_defendants(case_specific_info['title'])


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
            GROUP BY v.verdict, j.judge_name;
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
            GROUP BY t.tag_name, j.judge_name;
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
            GROUP BY c.court_name, j.judge_name;
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
            GROUP BY v.verdict, c.court_name;
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
            GROUP BY t.tag_name, c.court_name;
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
            GROUP BY j.judge_name, c.court_name;
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
            GROUP BY v.verdict, t.tag_name;
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
            GROUP BY j.judge_name, t.tag_name;
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
            ORDER BY month;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time_by_courts(conn: connection, filter: tuple):
    """
    Retrieves cases over time but filters by courts
    """
    query = """
                WITH original_data AS(
                    SELECT cc.court_date, c.court_name, COUNT(*) as case_count
                    FROM court_case as cc
                    JOIN court as c ON c.court_id = cc.court_id
                    GROUP BY cc.court_date, c.court_name
                    ORDER BY cc.court_date)
                SELECT * FROM original_data
                WHERE court_name IN %s;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time_by_judges(conn: connection, filter: tuple):
    """
    Retrieves cases over time but filters by judges
    """
    query = """
                WITH original_data AS(
                    SELECT cc.court_date, j.judge_name, COUNT(*) as case_count
                    FROM court_case as cc
                    JOIN judge_assignment as ja ON ja.court_case_id = cc.court_case_id
                    JOIN judge as j ON j.judge_id = ja.judge_id
                    GROUP BY cc.court_date, j.judge_name
                    ORDER BY cc.court_date)
                SELECT * FROM original_data
                WHERE judge_name IN %s;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time(conn: connection, filter: tuple):
    """
    Retrieves cases over time but filters by courts
    """
    query = """
                WITH original_data AS(
                    SELECT cc.court_date, c.court_name, COUNT(*) as case_count
                    FROM court_case as cc
                    JOIN court as c ON c.court_id = cc.court_id
                    GROUP BY cc.court_date, c.court_name
                    ORDER BY cc.court_date)
                SELECT * FROM original_data
                WHERE court_name IN %s;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def plot_filter_pie(df: pd.DataFrame, selected_filter: str, filter: str, tab: str, name: str):
    """
    Altair pie chart that displays the distribution of a field based on another (eg dist of verdict based on a given judge)
    """
    filtered_data = df[df[tab] == selected_filter]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative'),
        color=alt.Color(field=filter, type='nominal', title=name).scale(scheme="paired"),
        tooltip=[filter, 'count']
    ).properties(width=500).mark_arc(outerRadius=130)
    return pie_chart


def plot_pie(df: pd.DataFrame, filter: str, name: str):
    """
    Altair pie chart that displays the distribution of a filter (one of judge, tag or court type)
    """
    colour = alt.Color(field=filter, type='nominal',
                       title=name).scale(scheme='paired')
    if name == 'Verdict':
        domain = ['Guilty', 'Dismissed', 'Acquitted', 'Claimant Wins', 'Defendant Wins', 'Struck Out',
                  'Appeal Dismissed', 'Appeal Allowed', 'Other']
        range = ['#880808', '#efc800', '#006600 ', '#009900', '#00CC00', '#ff6f00', '#ff000d', '#89CFF0', '#BF40BF']

        colour = alt.Color(field=filter, type='nominal',
                           title=name).scale(domain=domain, range=range)

    aggregated_data = df.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    title = alt.TitleParams(f"{name} Distribution", anchor='start')
    pie_chart = alt.Chart(aggregated_data, title=title).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative', title='Count'),
        color=colour,
        tooltip=[filter, 'count'],

    ).properties(width=500, height=400).mark_arc(outerRadius=130)
    
    return pie_chart


def plot_filter_pie_tags(df: pd.DataFrame, selected_filter: list[str], filter: str, tab: str, name: str):
    """
    Altair pie chart that displays the distribution of tags based on either the judges, courts or verdict selected
    """
    filtered_data = df[df[tab].isin(selected_filter)]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        alt.Theta('count', type='quantitative', title='Tag Count'),
        color=alt.Color(field=filter, type='nominal', title=name),
        tooltip=[filter, 'count']
    ).properties(width=450, height=400).mark_arc(outerRadius=135)
    return pie_chart


def plot_cases_over_months(df: pd.DataFrame):
    title = alt.TitleParams('Cases Heard, Aggregated per Month', anchor='start')
    return alt.Chart(df.reset_index(), title=title).mark_bar().encode(
        x=alt.X('month', title='Month', sort=None,
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('case_count', title='Case Count')).properties(width=450, height=400)


def draw_line(data):
    data.loc[:, 'overall_sum'] = data['case_count'].cumsum()
    return alt.Chart(data).mark_line(opacity=0.5, thickness=0.01).encode(
        x=alt.X('court_date:T'),
        y=alt.Y('overall_sum:Q', title='Case Count'),
        color=alt.Color('court_name', title='Court'),
        tooltip=['court_name', 'overall_sum']
    )


def select_filter(df: pd.DataFrame, filter: str, filter_title: str):
    graph = list()
    for i in set(df[filter]):
        graph.append(draw_line(df[df[filter] == i], filter, filter_title))
    return alt.layer(*graph).properties(title=f'How the total amount of {filter_title} hearings compare over different {filter_title}s over time').interactive()


def select_court(df: pd.DataFrame):
    graph = list()
    for i in set(df['court_name']):
        graph.append(draw_line(df[df['court_name'] == i]))
    return alt.layer(*graph).properties(title='How the total amount of court hearings compare over different court types over time').interactive()


def subscribe_to_court(courts: list):
    st.header("Subscribe to Notifications")

    input = st.text_input("Enter your email to subscribe:")
    email = re.search(r"[\w_.-]+@[\w_.-]+[.]+[\w]+", input)
    st.markdown(
        """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
    courts = st.multiselect(
        "Select a court", courts, label_visibility="visible", placeholder='Choose courts to include')
    if st.button("Subscribe"):
        if email and courts:
            sns_client = get_sns_client()
            sub_to_topics(courts, sns_client, email.group())
            st.success(f"Subscribed successfully!")
        else:
            st.error("Please enter a valid email address and select a judge.")


def tabs():
    load_dotenv()
    conn = get_connection()
    insights, filtered_insights, comparisons, cases, subscribe = st.tabs(
        ["General Insights", "Filtered Insights", "Court Comparisons", "Cases", "Subscribe"])

    with cases:
        # col1, col2, col3 = st.columns([1,8,1])
        # with col2:
        available_cases = get_case_titles(conn)
        st.markdown("<h4>Court Case Summary</h4>", unsafe_allow_html=True)
        selected_case = st.selectbox("Court case summary: ", sorted(available_cases),
                                     placeholder='Select a case to be displayed', index=None,
                                     label_visibility="collapsed")
        if selected_case:
            html = format_case_presentation(conn, selected_case)
            if html:
                st.markdown(html, unsafe_allow_html=True)

    with insights:
        st.markdown('\n')
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 5, 5, 8, 0.5])
            with col2:
                verdict_df = get_judge_chart_data_verdict(conn)

                st.write(plot_pie(verdict_df, 'verdict', 'Verdict'))
                court_df = get_judge_data_court_type(conn)
                st.write(plot_pie(court_df, 'court_name', 'Court'))
            with col3:
                st.write('')
            with col4:
                tag_df = get_judge_chart_data_tag(conn)
                st.write(plot_pie(tag_df, 'tag_name', 'Tag'))
                case_count_df = get_cases_over_time(conn)
                case_count_df = case_count_df.replace([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [
                                                      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
                st.altair_chart(plot_cases_over_months(case_count_df))

    with comparisons:
        st.markdown(
            """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
        all_choices = list(set(get_court_data_judges(conn)['court_name']))
        court_choice = st.multiselect('Select a court to display', all_choices, default=[
                                      "High Court (Queen's Bench Division)", "High Court (King's Bench Division)"], placeholder='Select a court to include in the diagram')
        if court_choice:
            st.altair_chart(select_court(filtered_cases_over_time(
                conn, (court_choice))), use_container_width=True)


    with filtered_insights:
        col1, col2 = st.columns([0.7, 1])
        with col1:
            st.write(
                "<h5 style='padding-bottom: 6px; padding-top: 9px; padding-left: 10px'>Filter by:</h5>", unsafe_allow_html=True)
            filter = st.radio(
                "Filter by:", ["Judge", "Tag", "Court name"], horizontal=True, label_visibility='collapsed')
            judges = get_judges(conn)
            courts = get_courts(conn)
            tags = get_tags(conn)

        with col2:
            if filter == "Judge":
                selected_judge = st.selectbox(
                    "Select the judge to be displayed", judges, label_visibility="visible")
            if filter == "Court name":
                selected_court = st.selectbox(
                    "Select the court to be displayed", courts, label_visibility="visible")
            if filter == "Tag":
                st.markdown(
                    """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
                selected_tags = st.multiselect(
                    "Select tag(s) to be included", tags, label_visibility="visible", placeholder='Choose tags', default='Patents')
        st.subheader('')
        if filter == "Judge":
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.1, 5, 0.1])
            with col2:
                st.markdown(f"""<h6>Verdict Distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_verdict_df = get_judge_chart_data_verdict(conn)
                st.write(plot_filter_pie(judge_verdict_df,
                                         selected_judge, 'verdict', 'judge_name', 'Verdict'))
                st.markdown(f"""<h6>Tag Distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular tags")
                judge_tag_df = get_judge_chart_data_tag(conn)
                st.write(plot_filter_pie(judge_tag_df,
                                         selected_judge, 'tag_name', 'judge_name', 'Tag'))
            with col4:
                st.markdown(f"""<h6>Court Distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_court_df = get_judge_data_court_type(conn)
                st.write(plot_filter_pie(judge_court_df,
                                         selected_judge, 'court_name', 'judge_name', 'Court'))
                judge_choice = st.multiselect(
                    'Select a judge to display', judges, default=[
                        selected_judge, "Lord Sales"])
                st.altair_chart(select_filter(filtered_cases_over_time_by_judges(
                    conn, (judge_choice)), 'judge_name', 'judge'), use_container_width=True)

        if filter == "Court name":
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.1, 5, 0.1])
            with col2:
                st.markdown(f"""<h6>Verdict distribution for {
                            selected_court}</h6>""", unsafe_allow_html=True)
                court_verdict_df = get_court_data_verdict(conn)
                st.write(plot_filter_pie(court_verdict_df,
                                         selected_court, 'verdict', 'court_name', 'Verdict'))
                st.markdown(f"""<h6>Tag distribution for {
                            selected_court}</h6>""", unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular tags")
                court_tag_df = get_court_data_tags(conn)
                st.write(plot_filter_pie(court_tag_df,
                                         selected_court, 'tag_name', 'court_name', 'Tag'))
            with col4:
                st.markdown(f"""<h6>Judge distribution for {
                            selected_court}</h6>""", unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular judges")
                court_judge_df = get_court_data_judges(conn)
                st.write(plot_filter_pie(court_judge_df,
                                         selected_court, 'judge_name', 'court_name', 'Judge'))

        if filter == "Tag":
            if selected_tags:
                col1, col2, col3 = st.columns([4, 3, 8])
                with col1:
                    st.markdown('<h5>Grouped by Verdict</h5>',
                                unsafe_allow_html=True)
                    tag_verdict_df = get_tag_data_verdict(conn)
                    st.altair_chart(plot_filter_pie_tags(tag_verdict_df,
                                                         selected_tags, 'verdict', 'tag_name', 'Verdict'))
                with col3:
                    st.markdown('<h5>Grouped by Judge</h5>',
                                unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular judges")
                    tag_judge_df = get_tag_data_judges(conn)
                    st.altair_chart(plot_filter_pie_tags(
                        tag_judge_df, selected_tags, 'judge_name', 'tag_name', 'Judge'))
    with subscribe:
        subscribe_to_court(courts)


def display():
    col0, col1, col2, col3 = st.columns([1, 3, 4, 2.5])
    # with col1:
    #     st.image("justicev4.png", width=150)
    with col2:
        st.markdown('<h1>Justice Lens</h1>', unsafe_allow_html=True)
    with col3:
        st.image("justicev4.png", width=150)
    col5, col6, col7 = st.columns([1, 9, 1])
    with col6:
        tabs()


if __name__ == "__main__":
    conn = get_connection()
    display()
