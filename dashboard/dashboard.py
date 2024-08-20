import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from os import getenv
from dotenv import load_dotenv
import re
from csv import DictWriter
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
            JOIN judge as j on j.judge_id = ja.judge_id
            ;
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
    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        st.markdown(f"""**Case ID:** [{case_specific_info['court_case_id']}]({
                    case_specific_info['case_url']})""", help="Click here to view the original file")
    with col2:
        st.markdown(f"**Verdict:** <span style='color: red;'><strong><u>{
                    case_specific_info['verdict']}</u></strong>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Date:** {case_specific_info["court_date"].strftime('%d-%m-%Y')}")
    st.markdown(f"<h3><span style='color:white'><u>{
                case_specific_info["title"]}</u></span></h3>", unsafe_allow_html=True)
    st.html(f"<u>Court:</u> {case_specific_info['court_name']}")
    st.html(f"<u>Judge/s:</u> {judges_str[:-2]}")
    st.html(f"<u>Tags:</u> {tags_str[:-2]}")
    st.html(f"<u>Verdict summary:</u> {case_specific_info['verdict_summary']}")
    st.html(f"<u>Summary:</u> {case_specific_info["summary"]}")
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
            ORDER BY month
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
            ORDER BY cc.court_date;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(query)
        result = curs.fetchall()
    full_df = pd.DataFrame(result)
    for i,court in enumerate(full_df['court_name']):
        if court[:10] == 'High Court':
            temp_name = court.split('(')
            full_df.loc[i, 'court_name'] = 'HC (' + temp_name[1]
        elif court[:15] == 'Court of Appeal':
            temp_name = court.split('(')
            full_df.loc[i, 'court_name'] = 'CoA (' + temp_name[1]

    return full_df

def filtered_cases_over_time(conn:connection,filter:tuple):
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
    filtered_data = df[df[tab] == selected_filter]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values('count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative'),
        color=alt.Color(field=filter, type='nominal', title=name),
        tooltip=[filter, 'count']
    ).properties(width=500).mark_arc(outerRadius=100)
    return pie_chart


def plot_pie(df: pd.DataFrame, filter: str, name: str):
    aggregated_data = df.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values('count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        theta=alt.Theta(field='count',type='quantitative', title='Count'),
        color=alt.Color(field=filter, type='nominal',
                        title=name).scale(scheme='paired'),
        tooltip=[filter, 'count']
    ).properties(
        title=f"{name} distribution", width=500, height=400).mark_arc(outerRadius=100)
    return pie_chart


def plot_filter_pie_tags(df: pd.DataFrame, selected_filter: list[str], filter: str, tab: str, name: str):
    filtered_data = df[df[tab].isin(selected_filter)]
    aggregated_data = filtered_data.groupby(filter).sum().reset_index()
    aggregated_data = aggregated_data.sort_values('count', ascending=False).head(12)
    pie_chart = alt.Chart(aggregated_data).mark_arc().encode(
        alt.Theta('count', type='quantitative', title='Tag Count'),
        color=alt.Color(field=filter, type='nominal', title=name),
        tooltip=[filter, 'count']
    ).properties(width=450, height=400).mark_arc(outerRadius=135)
    return pie_chart


def plot_cases_over_months(df: pd.DataFrame):
    return alt.Chart(df.reset_index(), title='Months where more cases were heard').mark_bar().encode(
        x=alt.X('month', title='Month', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('case_count', title='Case Count')).properties(width=450, height=400).interactive()


def plot_cases_over_months_per_court(df: pd.DataFrame):
    return alt.Chart(df.reset_index()).mark_line().encode(
        x=alt.X('court_date:T', title='Case Date'),
        y=alt.Y('overall_sum:Q', title='Case Count')).properties(title='Cases per court type over time').configure_title(anchor='middle').interactive()

def multiple_courts(df:pd.DataFrame):
    click = alt.selection_multi(encodings=['color'])

    scatter = alt.Chart(df).mark_line().encode(
        x='court_date:T',
        y='case_count:Q',
        color=alt.Color('court_name:N').scale(scheme='rainbow')).transform_filter(click).interactive()

    hist = alt.Chart(df).mark_bar().encode(
        x='count()',
        y='court_name',
        color=alt.condition(click, 'court_name', alt.value('viridis'))).add_selection(click)

    return scatter & hist

def draw_line(data):
    data['overall_sum'] = data['case_count'].cumsum()
    return alt.Chart(data).mark_line(opacity=0.5, thickness=0.01).encode(
        x=alt.X('court_date:T'), #axis=alt.Axis(format="%d/%m", title='Day/Hour')),
        y=alt.Y('overall_sum:Q', title='Case Count'),
        color='court_name',
        tooltip=['court_name', 'overall_sum']
    )

def select_court(df:pd.DataFrame):
    graph = list()
    for i in set(df['court_name']):
        graph.append(draw_line(df[df['court_name']==i]))
    
    combined_graph = alt.layer(*graph).properties(title='How the total amount of court hearings compare over different court types').interactive()
    
    return combined_graph

     
    return alt.Chart(df).mark_line().encode(
        x='court_date:T',
        y='overall_sum:Q',
        color=alt.Color('court_name:N').scale(scheme='rainbow')).interactive()


def subscribe_to_court(courts: list):
    st.header("Subscribe to Notifications")

    input = st.text_input("Enter your email to subscribe:")
    email = re.search(r"[\w_.-]+@[\w_.-]+[.]+[\w]+", input)
    st.markdown(
        """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
    courts = st.multiselect(
        "Select a court", courts, label_visibility="hidden", placeholder='Choose courts to include')
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
    cases, insights, filtered_insights, subscribe = st.tabs(
        ["Cases", "General Insights", "Filtered Insights", "Subscribe"])

    with cases:
        # col1, col2, col3 = st.columns([1,8,1])
        # with col2:
        available_cases = get_case_titles(conn)
        st.markdown("<h4>Court case summary: </h4>", unsafe_allow_html=True)
        selected_case = st.selectbox("Court case summary: ", sorted(available_cases),
                                     placeholder='Select a case to be displayed', index=None,
                                     label_visibility="collapsed")
        if selected_case:
            html = format_case_presentation(conn, selected_case)
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
                case_count_df = case_count_df.replace([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
                st.altair_chart(plot_cases_over_months(case_count_df))
        court_cases_over_time_df = get_cases_over_time_per_court(conn)
        all_courts = court_cases_over_time_df[['court_date','case_count']].sort_values(by=['court_date'], ascending=True)
        all_courts['overall_sum'] = all_courts['case_count'].cumsum()
        st.altair_chart(plot_cases_over_months_per_court(all_courts), use_container_width=True)
        all_data = court_cases_over_time_df.sort_values(by=['court_date'], ascending=True)
        st.altair_chart(multiple_courts(all_data), use_container_width=True)
        st.markdown("""<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
        all_choices = list(set(get_court_data_judges(conn)['court_name']))
        court_choice = st.multiselect('Select a court to display', all_choices, default=all_choices, help='Abbreviated. HC = High Court, CoA = Court of Appeal')
        st.altair_chart(select_court(filtered_cases_over_time(conn,(court_choice))), use_container_width=True)
        selected = list()
        col1, col2 = st.columns([1,3])
        with col1:
            for i in all_choices:
                on = st.checkbox(i,value=False)
                if not on:
                    selected.append(i)
        with col2:
            st.altair_chart(select_court(filtered_cases_over_time(conn,(selected))), use_container_width=True)

    with filtered_insights:
        # st.markdown("""<div style='padding-bottom:-50px;'>Filter by:</div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([0.7, 1])

        with col1:
            st.write(
                "<h5 style='padding-bottom: 6px; padding-top: 9px; padding-left: 10px'>Filter by:</h5>", unsafe_allow_html=True)
            filter = st.radio(
                "Filter by:", ["Judge", "Tag", "Court name"], horizontal=True, label_visibility='collapsed')
            judges = get_judges(conn)
            courts = get_courts(conn)
            tags = get_tags(conn)
            # st.markdown(f"""<div style='padding-top: 35px;'>Displaying analytics for <span style='color: red;'>{
            #             filter}</span>:</div>""", unsafe_allow_html=True)

        with col2:
            if filter == "Judge":
                selected_judge = st.selectbox(
                    "Select a judge", judges, label_visibility="hidden")
            if filter == "Court name":
                selected_court = st.selectbox(
                    "Select a court", courts, label_visibility="hidden")
            if filter == "Tag":
                st.markdown(
                    """<style>span[data-baseweb="tag"] {background-color: black !important;}</style>""", unsafe_allow_html=True)
                selected_tags = st.multiselect(
                    "Select a tag", tags, label_visibility="hidden", placeholder='Choose tags to include', default='Patents')
        st.subheader('')
        if filter == "Judge":
            col1, col2, col3, col4, col5 = st.columns([0.1, 5, 0.1, 5, 0.1])
            with col2:
                st.markdown(f"""<h6>Verdict distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_verdict_df = get_judge_chart_data_verdict(conn)
                st.write(plot_filter_pie(judge_verdict_df,
                                         selected_judge, 'verdict', 'judge_name', 'Verdict'))
                st.markdown(f"""<h6>Tag distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular tags")
                judge_tag_df = get_judge_chart_data_tag(conn)
                st.write(plot_filter_pie(judge_tag_df,
                                         selected_judge, 'tag_name', 'judge_name', 'Tag'))
            with col4:
                st.markdown(f"""<h6>Court distribution for Judge {
                            selected_judge}</h6>""", unsafe_allow_html=True)
                judge_court_df = get_judge_data_court_type(conn)
                st.write(plot_filter_pie(judge_court_df,
                                         selected_judge, 'court_name', 'judge_name', 'Court'))

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
                # title = "<h4>Insights for Tags: "
                # for tag in selected_tags:
                #     title += tag + ", "
                # st.markdown(f"{title[:-2]}</h4>", unsafe_allow_html=True)
                # st.subheader('')
                col1, col2, col3 = st.columns([4, 3, 8])
                with col1:
                    st.markdown('<h5>Grouped by verdict</h5>',
                                unsafe_allow_html=True)
                    tag_verdict_df = get_tag_data_verdict(conn)
                    st.altair_chart(plot_filter_pie_tags(tag_verdict_df,
                                                         selected_tags, 'verdict', 'tag_name', 'Verdict'))
                with col3:
                    st.markdown('<h5>Grouped by judge</h5>',
                             unsafe_allow_html=True, help="Note - to make the graphs more useful, they only show the 12 most popular judges")
                    tag_judge_df = get_tag_data_judges(conn)
                    st.altair_chart(plot_filter_pie_tags(
                        tag_judge_df, selected_tags, 'judge_name', 'tag_name', 'Judge'))
    with subscribe:
        subscribe_to_court(courts)


def display():
    col1, col2, col3 = st.columns([2, 3, 1])
    with col2:
        st.title('Court Transcripts :judge:')
    col1, col2, col3 = st.columns([1, 9, 1])
    with col2:
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
