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


def get_judges(cnx: connection) -> list[str]:
    """
    Retrieves a list of judges from the database
    """
    query = """
            SELECT j.judge_name
            FROM judge_assignment as ja
            JOIN judge as j on j.judge_id = ja.judge_id;
    """
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    judges = []
    for row in result:
        if row['judge_name'] not in judges:
            judges.append(row['judge_name'])
    return judges


def get_courts(cnx: connection) -> list[str]:
    """
    Retrieves a list of courts from the database
    """
    query = """
            SELECT c.court_name 
            FROM court as c
            JOIN court_case as cc ON c.court_id = cc.court_id;
    """
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    courts = []
    for row in result:
        if row['court_name'] not in courts:
            courts.append(row['court_name'])
    return courts


def get_tags(cnx: connection) -> list[str]:
    """
    Retrieves a list of tags from the database
    """
    query = """SELECT tag_name FROM tag;"""
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return [row["tag_name"] for row in result]


def get_case_titles(cnx: connection) -> list[str]:
    """
    Retrieves a list of case titles from the database
    """
    query = """SELECT title FROM court_case;"""
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return [row["title"] for row in result]


def get_cases_info_for_case(cnx: connection, title: str) -> dict:
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()
    return result[0]


def get_judges_for_case(cnx: connection, title: str) -> list[str]:
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()
    return [row["judge_name"] for row in result]


def get_tags_for_case(cnx: connection, title: str) -> list[str]:
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title,))
        result = curs.fetchall()
    return [row["tag_name"] for row in result]


def get_participants_and_lawyers_for_case(cnx: connection, title: str,
                                          is_defendant: bool) -> list[dict]:
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (title, is_defendant))
        result = curs.fetchall()
    return result


def format_participants_to_string(participants: list[dict]) -> str:
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
            prosecuting_participants)
        st.markdown(prosecuting_participants_html,
                    unsafe_allow_html=True)
    with col2:
        pass
    with col3:
        st.markdown("""<span style='color:white'>Defendants</span>""",
                    unsafe_allow_html=True)
        defending_participants = get_participants_and_lawyers_for_case(
            conn, selected_case, True)
        defending_participants_html = format_participants_to_string(
            defending_participants)
        st.markdown(defending_participants_html,
                    unsafe_allow_html=True)


def format_case_presentation(cnx: connection, title: str) -> str:
    """
    Code used to render how and what information will be displayed of each cases
    """
    case_specific_info = get_cases_info_for_case(cnx, title)
    judges = get_judges_for_case(cnx, title)
    tags = get_tags_for_case(cnx, title)
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
                    case_specific_info['case_url']})""",
                    help="Click here to view the original file")
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
    return ''


def get_judge_chart_data_verdict(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_judge_chart_data_tag(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_judge_data_court_type(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_court_data_verdict(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_court_data_tags(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_court_data_judges(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_tag_data_verdict(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_tag_data_judges(cnx: connection):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def get_cases_over_time(cnx: connection):
    """
    Retrieves cases over time
    """
    query = """
            SELECT extract(month FROM court_date) as month, COUNT(*) as case_count
            FROM court_case as cc
            GROUP BY month 
            ORDER BY month;
    """
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time_by_courts(cnx: connection, court_filter: tuple):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(court_filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time_by_judges(cnx: connection, judge_filter: tuple):
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
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(judge_filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def filtered_cases_over_time_by_tags(cnx: connection, tag_filter: tuple):
    """
    Retrieves cases over time but filters by tags
    """
    query = """
                WITH original_data AS(
                    SELECT cc.court_date, t.tag_name, COUNT(*) as case_count
                    FROM court_case as cc
                    JOIN tag_assignment as ta ON ta.court_case_id = cc.court_case_id
                    JOIN tag as t ON t.tag_id = ta.tag_id
                    GROUP BY cc.court_date, t.tag_name
                    ORDER BY cc.court_date)
                SELECT * FROM original_data
                WHERE tag_name IN %s;
    """
    with cnx.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query, (tuple(tag_filter),))
        result = curs.fetchall()
    return pd.DataFrame(result)


def plot_filter_pie(df: pd.DataFrame, selected_filter: str, field: str, tab: str, name: str):
    """
    Altair pie chart that displays the distribution of a field based on another 
    (eg dist of verdict based on a given judge)
    """
    filtered_data = df[df[tab] == selected_filter]
    aggregated_data = filtered_data.groupby(field).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative'),
        color=alt.Color(field=field, type='nominal', title=name),
        tooltip=[field, 'count']
    ).properties(width=500).mark_arc(outerRadius=100)
    return pie_chart


def plot_pie(df: pd.DataFrame, field: str, name: str):
    """
    Altair pie chart that displays the distribution of a filter (one of judge, tag or court type)
    """
    colour = alt.Color(field=field, type='nominal',
                       title=name).scale(scheme='paired')
    if name == 'Verdict':
        domain = ['Guilty', 'Dismissed', 'Acquitted', 'Claimant Wins', 'Defendant Wins',
                  'Struck Out', 'Appeal Dismissed', 'Appeal Allowed', 'Other']
        colour_range = ['#FF3131', '#e6e65e', '#006600 ', '#009900',
                 '#00CC00', '#ff6f00', '#ff000d', '#89CFF0', '#BF40BF']

        colour = alt.Color(field=field, type='nominal',
                           title=name).scale(domain=domain, range=colour_range)

    aggregated_data = df.groupby(field).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative',
                        title='Count').stack(True),
        color=colour,
        tooltip=[field, 'count'],
        # order=alt.Order('count', sort='descending')
    ).properties(
        title=f"{name} Distribution", width=500, height=400).mark_arc(outerRadius=130)

    return pie_chart


def plot_filter_pie_tags(df: pd.DataFrame, selected_filter: list[str], field: str, tab: str,
                         name: str):
    """
    Pie chart that displays the distribution of tags based on either the judges, courts or verdicts
    """
    filtered_data = df[df[tab].isin(selected_filter)]
    aggregated_data = filtered_data.groupby(field).sum().reset_index()
    aggregated_data = aggregated_data.sort_values(
        'count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        alt.Theta('count', type='quantitative', title='Tag Count'),
        color=alt.Color(field=field, type='nominal', title=name),
        tooltip=[field, 'count']
    ).properties(width=450, height=400).mark_arc(outerRadius=135)
    return pie_chart


def plot_cases_over_months(df: pd.DataFrame):
    """Plot of all the case count, when aggregated by month"""
    title = alt.TitleParams(
        'Cases Heard, Aggregated per Month', anchor='start')
    return alt.Chart(df.reset_index(), title=title).mark_bar().encode(
        x=alt.X('month', title='Month', sort=None,
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('case_count', title='Case Count')).properties(width=450, height=400)


def draw_line(data:pd.DataFrame, field: str, filter_title: str):
    """Graph with a singular line: field cumulative count vs time"""
    data.loc[:, 'overall_sum'] = data['case_count'].cumsum()
    return alt.Chart(data).mark_line(opacity=1, thickness=0.01).encode(
        x=alt.X('court_date:T', title='Date of the Case'),
        y=alt.Y('overall_sum:Q', title='Case Count'),
        color=alt.Color(field, title=filter_title.title()),
        tooltip=[field, 'overall_sum']
    )


def select_filter(df: pd.DataFrame, field: str, filter_title: str):
    """Function that groups different databases into one line chart, one per field selected"""
    graph = []
    for i in set(df[field]):
        graph.append(draw_line(df[df[field] == i], field, filter_title))
    return alt.layer(*graph).properties(
        title=f"""Cases for Selected {filter_title.title()}s, Over Time""")


def subscribe_to_court(courts: list):
    """Allowing a SNS subscription to specific courts"""
    st.header("Subscribe to Notifications")

    email_input = st.text_input("Enter your email to subscribe:")
    email = re.search(r"[\w_.-]+@[\w_.-]+[.]+[\w]+", email_input)
    st.markdown(
        """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""",
        unsafe_allow_html=True)
    courts = st.multiselect(
        "Select a court", courts, label_visibility="hidden", placeholder='Choose courts to include')
    if st.button("Subscribe"):
        if email and courts:
            sns_client = get_sns_client()
            sub_to_topics(courts, sns_client, email.group())
            st.success("Subscribed successfully!")
        else:
            st.error("Please enter a valid email address and select a judge.")


def tabs():
    """Separating our content into tabs"""
    load_dotenv()
    cnx = get_connection()
    insights, filtered_insights, cases, subscribe = st.tabs(
        ["General Insights", "Filtered Insights", "Cases", "Subscribe"])

    with cases:
        # col1, col2, col3 = st.columns([1,8,1])
        # with col2:
        available_cases = get_case_titles(cnx)
        st.markdown("<h4>Court Case Summary</h4>", unsafe_allow_html=True)
        selected_case = st.selectbox("Court case summary: ", sorted(available_cases),
                                     placeholder='Select a case to be displayed', index=None,
                                     label_visibility="hidden")
        if selected_case:
            html = format_case_presentation(cnx, selected_case)
            if html:
                st.markdown(html, unsafe_allow_html=True)

    with insights:
        st.markdown('\n')
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 5, 5, 8, 0.5])
            with col1:
                pass
            with col2:
                verdict_df = get_judge_chart_data_verdict(cnx)
                st.write(plot_pie(verdict_df, 'verdict', 'Verdict'))
                court_df = get_judge_data_court_type(cnx)
                st.write(plot_pie(court_df, 'court_name', 'Court'))
            with col3:
                st.write('')
            with col4:
                tag_df = get_judge_chart_data_tag(cnx)
                st.write(plot_pie(tag_df, 'tag_name', 'Tag'))
                case_count_df = get_cases_over_time(cnx)
                case_count_df = case_count_df.replace([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
                st.altair_chart(plot_cases_over_months(case_count_df))
            with col5:
                pass

    with filtered_insights:
        col1, col2 = st.columns([0.4, 1])
        with col1:
            st.write("""<h5 style='padding-bottom: 6px; padding-top: 9px; padding-left: 10px'>
                     Filter by:</h5>""",unsafe_allow_html=True)
            filter_by = st.radio(
                "Filter by:", ["Judge", "Tag", "Court name"], horizontal=True,
                label_visibility='collapsed')
            judges = get_judges(cnx)
            courts = get_courts(cnx)
            tags = get_tags(cnx)

        with col2:
            if filter_by == "Judge":
                selected_judge = st.selectbox(
                    "Select a judge to display graphs for", judges, label_visibility="visible")
            if filter_by == "Court name":
                selected_court = st.selectbox(
                    "Select a court to display graphs for", courts, label_visibility="visible")
            if filter_by == "Tag":
                st.markdown(
                """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""",
                    unsafe_allow_html=True)
                selected_tags = st.multiselect(
                    "Select at least a tag", tags, label_visibility="visible",
                    placeholder='Choose tags to include', default='Patents')
        # st.subheader('')
        if filter_by == "Judge":
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.5, 5, 0.1])
            with col2:
                st.markdown(
                """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""",
                    unsafe_allow_html=True)
                judge_choice = st.multiselect(
                    'Select judges to display', judges, default=[
                        selected_judge, "Lord Sales"])
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.5, 5, 0.1])
            with col4:
                st.markdown(f"""<h6>Verdict distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_verdict_df = get_judge_chart_data_verdict(cnx)
                st.write(plot_filter_pie(judge_verdict_df,
                                         selected_judge, 'verdict', 'judge_name', 'Verdict'))
            with col2:
                if judge_choice:
                    st.altair_chart(select_filter(filtered_cases_over_time_by_judges(
                        cnx, (judge_choice)), 'judge_name', 'Judge'), use_container_width=True)

            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.1, 5, 0.1])
            with col2:
                st.markdown(f"""<h6>Tag distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True,
                help="Note - This is only showing the 12 most popular tags")
                judge_tag_df = get_judge_chart_data_tag(cnx)
                st.write(plot_filter_pie(judge_tag_df,
                                         selected_judge, 'tag_name', 'judge_name', 'Tag'))
            with col4:
                st.markdown(f"""<h6>Court distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_court_df = get_judge_data_court_type(cnx)
                st.write(plot_filter_pie(judge_court_df,
                                         selected_judge, 'court_name', 'judge_name', 'Court'))

        if filter_by == "Court name":
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.5, 5, 0.1])
            with col2:
                st.markdown(
                """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""",
                    unsafe_allow_html=True)
                all_choices = list(set(get_court_data_judges(cnx)['court_name']))
                court_choice = st.multiselect('Select courts to display', all_choices, default=[
                    "High Court (Queen's Bench Division)", "High Court (King's Bench Division)"])
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.5, 5, 0.1])
            with col4:
                st.markdown(f"""<h6>Verdict distribution for {
                            selected_court}</h6>""", unsafe_allow_html=True)
                court_verdict_df = get_court_data_verdict(cnx)
                st.write(plot_filter_pie(court_verdict_df,
                                         selected_court, 'verdict', 'court_name', 'Verdict'))
            with col2:
                if court_choice:
                    st.altair_chart(select_filter(filtered_cases_over_time_by_courts(
                        cnx, (court_choice)), 'court_name', 'court'), use_container_width=True)

            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.1, 5, 0.1])
            with col2:
                st.markdown(
                    f"""<h6>Tag distribution for {selected_court}</h6>""", unsafe_allow_html=True,
                            help="Note - This is only showing the 12 most popular tags")
                court_tag_df = get_court_data_tags(cnx)
                st.write(plot_filter_pie(court_tag_df,
                                            selected_court, 'tag_name', 'court_name', 'Tag'))
            with col4:
                st.markdown(
                    f"""<h6>Judge distribution for {selected_court}</h6>""", unsafe_allow_html=True,
                    help="Note - This is only showing the 12 most popular judges")
                court_judge_df = get_court_data_judges(cnx)
                st.write(plot_filter_pie(court_judge_df,
                                         selected_court, 'judge_name', 'court_name', 'Judge'))


        if filter_by == "Tag":
            if selected_tags:
                st.altair_chart(select_filter(filtered_cases_over_time_by_tags(
                    cnx, (selected_tags)), 'tag_name', 'tag'), use_container_width=True)
                col1, col2, col3 = st.columns([4, 3, 8])
                with col1:
                    st.markdown('<h5>Grouped by verdict</h5>',
                                unsafe_allow_html=True)
                    tag_verdict_df = get_tag_data_verdict(cnx)
                    st.altair_chart(plot_filter_pie_tags(tag_verdict_df, selected_tags,
                                                         'verdict', 'tag_name', 'Verdict'))
                with col3:
                    st.markdown('<h5>Grouped by judge</h5>',unsafe_allow_html=True,
                                help="Note - This is only showing the 12 most popular judges")
                    tag_judge_df = get_tag_data_judges(cnx)
                    st.altair_chart(plot_filter_pie_tags(
                        tag_judge_df, selected_tags, 'judge_name', 'tag_name', 'Judge'))

    with subscribe:
        subscribe_to_court(courts)


def display():
    """Function to display our whole dashboard"""
    col0, col1, col2, col3 = st.columns([1, 3, 4, 2.5])
    with col0:
        pass
    with col1:
        pass
    with col2:
        st.markdown('<h1>Justice Lens</h1>', unsafe_allow_html=True)
    with col3:
        st.image("justicev4.png", width=150)
    col5, col6, col7 = st.columns([1, 9, 1])
    with col5:
        pass
    with col6:
        tabs()
    with col7:
        pass


if __name__ == "__main__":
    conn = get_connection()
    display()
