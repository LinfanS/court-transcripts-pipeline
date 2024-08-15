"Script that will take the transformed data and load it to the rds"
import nltk
nltk.download('wordnet')
import datetime
from os import environ
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import connection
from dotenv import load_dotenv
from judge_matching import match_judge, get_judges
from nltk.corpus import wordnet
from Levenshtein import jaro_winkler


def synonym_extractor(phrase:str)-> set[str]:
    synonyms = []
    for syn in wordnet.synsets(phrase):
        for l in syn.lemmas():
            synonyms.append(l.name())
    synonyms = set(synonyms)
    if phrase in synonyms:
        synonyms.remove(str(phrase))
    return synonyms

def remove_synonyms(words:list[str]) -> list[str]:
    for word in words: #replace any synonyms
        synonyms = synonym_extractor(word)
        if synonyms:
            for syn in synonyms:
                if str(syn) in set(words):
                    words = list(map(lambda x: x.replace(word, syn), words))
                    #print(syn, 'has been replaced with', word, 'as found to be synonymous')
        
        for word2 in words: #replace any too-similar words
            if not word == word2:
                jw = jaro_winkler(word,word2)
                if jw > 0.9:
                    words = list(map(lambda x: x.replace(word, word2), words))
                    #print(word2, 'has been replaced with', word, 'as found to have a jw >0.9')
    return words

def get_connection() -> connection:
    """Establishes a connection to the database"""
    return connect(
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        host=environ["DB_HOST"],
        port=environ["DB_PORT"],
        database=environ["DB_NAME"],
        cursor_factory=RealDictCursor,
    )

def reset_schema(conn: connection):
    """running schema to empty/reset the tables"""
    with open("schema.sql", "r", encoding="utf-8") as file:
        code = file.read()
        with conn.cursor() as cur:
            cur.execute(code)

def return_single_ids(map: dict, to_convert: tuple[str]) -> tuple[int]:
    to_return = []
    for item in to_convert:
        to_return.append(map[item])
    return tuple(to_return)

def return_multiple_ids(map: dict, to_convert: tuple[tuple[str]]) -> tuple[tuple[int]]:
    to_return = []
    for case in to_convert:
        group = []
        for item in case:
            group.append(map[item])
        to_return.append(tuple(group))
    return tuple(to_return)

def get_verdict_mapping(conn: connection) -> dict:
    """To map each verdict to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT verdict, verdict_id FROM verdict")
        rows = cur.fetchall()
    return {row["verdict"]: row["verdict_id"] for row in rows}

def get_court_mapping(conn: connection) -> dict:
    """To map each court to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT court_name, court_id FROM court")
        rows = cur.fetchall()
    return {row["court_name"]: row["court_id"] for row in rows}

def get_judge_mapping(conn: connection) -> dict:
    """To map each judge to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT judge_name, judge_id FROM judge")
        rows = cur.fetchall()
    return {row["judge_name"]: row["judge_id"] for row in rows}

def get_tag_mapping(conn: connection) -> dict:
    """To map each tag to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT tag_name, tag_id FROM tag")
        rows = cur.fetchall()
    return {row["tag_name"]: row["tag_id"] for row in rows}

def get_law_firm_mapping(conn: connection) -> dict:
    """To map each law firm to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT law_firm_name, law_firm_id FROM law_firm")
        rows = cur.fetchall()
    return {row["law_firm_name"]: row["law_firm_id"] for row in rows}

def get_participant_mapping(conn: connection) -> dict:
    """To map each participant to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT participant_name, participant_id FROM participant")
        rows = cur.fetchall()
    return {row["participant_name"]: row["participant_id"] for row in rows}

def get_lawyer_mapping(conn: connection) -> dict:
    """To map each lawyer (and firm as a pair) to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT lawyer_name, lawyer_id FROM lawyer")
        rows = cur.fetchall()
    return {row["lawyer_name"]: row["lawyer_id"] for row in rows}

def add_judges(conn: connection, all_judges_list: list[tuple[str]]):
    """Adds new judges to the table judge"""
    matched_judges_list = [
        (match_judge(judge_name[0], get_judges(conn)),)
        for judge_name in all_judges_list]
    query = """
    INSERT INTO judge(judge_name) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched_judges_list)
    conn.commit()

    return matched_judges_list

def add_tags(conn: connection, all_tags_list: list[tuple[str]]):
    """Adds new tags to the tag table"""
    query = """
    INSERT INTO tag(tag_name) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, all_tags_list)
    conn.commit()

def add_law_firms(conn: connection, all_firm_names: list[tuple[str]]):
    """Adds new law firm names to the law_firm table"""
    query = """
    INSERT INTO law_firm(law_firm_name) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, all_firm_names)
    conn.commit()

def add_participants(conn: connection, all_participant_names: list[tuple[str]]):
    """Adds new people names to the participants table"""
    query = """
    INSERT INTO participant(participant_name) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, all_participant_names)
    conn.commit()

def add_courts(conn: connection, all_court_names: list[tuple[str]]):
    """Adds new court names to the court table"""
    query = """
    INSERT INTO court(court_name) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, all_court_names)
    conn.commit()

def populate_court_case(
    conn: connection,
    ids: tuple[tuple[str]],
    summaries: tuple[tuple[str]],
    v_ids: tuple[tuple[int]],
    titles: tuple[tuple[str]],
    dates: tuple[tuple[str]],
    numbers: tuple[tuple[str]],
    urls: tuple[tuple[str]],
    c_ids: tuple[tuple[str]],
    v_summmaries: tuple[tuple[str]],
):  # no return
    """Add data to the court_case table to be able to then obtain all ids"""
    matched = []
    for i, value in enumerate(ids):
        matched.append(
            (
                value,
                summaries[i],
                v_ids[i],
                titles[i],
                dates[i],
                numbers[i],
                urls[i],
                c_ids[i],
                v_summmaries[i],
            )
        )
    query = """
    INSERT INTO court_case(court_case_id, summary, verdict_id, title, court_date, case_number, case_url, court_id, verdict_summary) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()

def populate_judge_assignment(conn: connection, case_id: int, judges: tuple[int]):
    matched = []
    for judge in judges:
        matched.append((case_id, judge))
    query = """
    INSERT INTO judge_assignment(court_case_id, judge_id) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()

def populate_tag_assignment(conn: connection, case_id: int, tags: tuple[int]):
    matched = []
    for tag in tags:
        matched.append((case_id, tag))
    query = """
    INSERT INTO tag_assignment(court_case_id, tag_id) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()

def populate_lawyer(conn: connection, all_lawyers: list[str], all_law_firms: list[int]):
    """Add data to the lawyer table that matches lawyers to their firm"""
    matched = []
    for i, value in enumerate(all_lawyers):
        matched.append((value, all_law_firms[i]))
    query = """
    INSERT INTO lawyer(lawyer_name, law_firm_id) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()

def populate_participant_assignment(
    conn: connection, case_id, all_participant_ids, all_lawyer_ids, all_person_type
):
    matched = []
    for i, accusant in enumerate(all_participant_ids):
        matched.append((case_id, accusant, all_lawyer_ids[i], all_person_type[i]))
    query = """
    INSERT INTO participant_assignment(court_case_id, participant_id, lawyer_id, is_defendant) VALUES %s
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()

def process_people_data(people):
    lawyer_list, law_firm_list, people_list = ([], []), ([], []), ([], [])
    for case in people:
        for side in range(len(case)):
            for i, person in enumerate(case[side]):
                if (i + 1) % 2 == 0:
                    lawyer_list[0].append(bool(side))
                    lawyer_list[1].append(person[0])
                    law_firm_list[0].append((person[1],))
                    law_firm_list[1].append(person[1])
                if (i + 2) % 2 == 0:
                    people_list[0].append((person,))
                    people_list[1].append(person)
    return lawyer_list, law_firm_list, people_list

def replace_data(
    unmatched_judges: list[tuple[str]], matched_judges: list[tuple[str]]
) -> list[tuple[str]]:
    result = []
    matched_judges_index = 0

    for judge_tuple in unmatched_judges:
        new_tuple = tuple(
            matched_judges[matched_judges_index + i][0] for i in range(len(judge_tuple))
        )
        result.append(new_tuple)
        matched_judges_index += len(judge_tuple)

    return result

def insert_to_database(conn: connection, transformed_data: dict) -> None:

    verdict_map = get_verdict_mapping(conn)
    add_courts(conn, [(court,) for court in transformed_data["courts"]])
    court_map = get_court_mapping(conn)

    judges = transformed_data["judges"]
    matched_judges_list = add_judges(
        conn, [(judge,) for case in judges for judge in case]
    )
    updated_judge_names = replace_data(judges, matched_judges_list)

    judges_map = get_judge_mapping(conn)

    tags = transformed_data["tags"] 
    #get all tags and replace any synonyms
    all_tags = []
    for case in tags:
        for tag in case:
            all_tags.append(tag)
    temp_tags = remove_synonyms(all_tags)

    #put back in format expected
    reconstructed = []
    i = 0
    for case in tags:
        group = []
        for tag in case:
            group.append(temp_tags[i])
            i+=1
        reconstructed.append(tuple(group))
    
    tags = reconstructed

    add_tags(conn, [(tag,) for case in tags for tag in case])

    tag_map = get_tag_mapping(conn)

    lawyer_list, law_firm_list, people_list = process_people_data(
        transformed_data["people"]
    )

    add_law_firms(conn, law_firm_list[0])
    law_firm_map = get_law_firm_mapping(conn)
    add_participants(conn, people_list[0])
    participant_map = get_participant_mapping(conn)

    court_ids = return_single_ids(court_map, transformed_data["courts"])
    for i,verdict in enumerate(transformed_data["verdicts"]):
        if verdict not in ('Guilty','Not Guilty','Dismissed','Acquitted', 'Hung Jury', 'Claimant Wins','Defendant Wins','Settlement','Struck Out','Appeal Dismissed','Appeal Allowed','Other'):
            transformed_data["verdicts"][i] = 'Other'
    verdict_ids = return_single_ids(verdict_map, transformed_data["verdicts"])
    j_ids = return_multiple_ids(judges_map, updated_judge_names)
    tag_ids = return_multiple_ids(tag_map, tags)
    law_firm_ids = return_single_ids(law_firm_map, law_firm_list[1])
    participant_ids = return_single_ids(participant_map, people_list[1])

    populate_lawyer(conn, lawyer_list[1], law_firm_ids)
    lawyer_map = get_lawyer_mapping(conn)
    lawyer_ids = return_single_ids(lawyer_map, lawyer_list[1])

    populate_court_case(
        conn,
        transformed_data["case_ids"],
        transformed_data["summ"],
        verdict_ids,
        transformed_data["title"],
        transformed_data["date"],
        transformed_data["number"],
        transformed_data["url"],
        court_ids,
        transformed_data["v_sum"],
    )

    for i, case_id in enumerate(transformed_data["case_ids"]):
        populate_judge_assignment(conn, case_id, j_ids[i])
        populate_tag_assignment(conn, case_id, tag_ids[i])
        populate_participant_assignment(
            conn, case_id, participant_ids, lawyer_ids, lawyer_list[0]
        )

    return "done"

if __name__ == "__main__":
    load_dotenv()
    transform = {
        "verdicts": ["Dismissed", "Dismissed"],
        "courts": [
            "High Court (Administrative Court)",
            "Court of Appeal (Civil Division)",
        ],
        "case_ids": ["[2009] EWHC 719 (Admin)", "[2009] EWCA Civ 309"],
        "summ": [
            "This case involved a judicial review application by the Stamford Chamber of Trade and Commerce and F H Gilman & Co against the Secretary of State for Communities and Local Government and South Kesteven District Council. The claimants challenged the decision not to save Policy T1 of the Local Plan, which safeguarded a proposed road scheme. The court found that the decision was rational and did not require public consultation, leading to the dismissal of the claim.",
            "This case involved appeals from the Employment Appeal Tribunal regarding equal pay claims made by employees against their employers, Suffolk Mental Health Partnership NHS Trust and Sandwell Metropolitan Borough Council. The central issue was whether the claimants had properly followed the statutory grievance procedures outlined in the Employment Act 2002. The court found that the claimants had indeed complied with the necessary requirements, allowing their claims to be heard despite the employers' objections.",
        ],
        "title": [
            "Stamford Chamber of Trade & Commerce, R (on the application of) v The Secretary of State for Communities and Local Government",
            "Suffolk Mental Health Partnership NHS Trust v Hurst & Ors",
        ],
        "date": [datetime.date(2009, 4, 7), datetime.date(2009, 4, 7)],
        "number": ["CO/10442/2007", "A2/2008/2870 & A2/2008/2877"],
        "url": [
            "https://caselaw.nationalarchives.gov.uk/ewhc/admin/2009/719",
            "https://caselaw.nationalarchives.gov.uk/ewca/civ/2009/309",
        ],
        "v_sum": [
            "The court dismissed the claim for judicial review, concluding that the Secretary of State's decision not to save Policy T1 of the Local Plan was rational and lawful, and that there was no legitimate expectation for public consultation prior to this decision.",
            "The court upheld the Employment Appeal Tribunal's decision that the claimants had complied with the statutory grievance procedures under the Employment Act 2002, allowing their equal pay claims to proceed.",
        ],
        "judges": [
            ("Rabinder Singh",),
            ("Lord Justice Pill", "Lord Justice Wall", "Lord Justice Etherton"),
        ],
        "tags": [
            (
                "judicial review",
                "planning policy",
                "local government",
                "public consultation",
                "transportation",
                "legitimate expectation",
                "development plan",
                "administrative law",
                "court ruling",
            ),
            (
                "equal pay",
                "employment law",
                "grievance procedures",
                "tribunal",
                "NHS",
                "discrimination",
                "collective claims",
                "jurisdiction",
                "statutory compliance",
            ),
        ],
        "people": [
            (
                (
                    "The Queen",
                    ("Michael Bedford", "Matthew Arnold Baldwin"),
                    "Stamford Chamber of Trade and Commerce",
                    ("Michael Bedford", "Matthew Arnold Baldwin"),
                ),
                (
                    "F H Gilman & Co",
                    ("John Litton", "Treasury Solicitor"),
                    "The Secretary of State for Communities and Local Government",
                    ("John Litton", "Treasury Solicitor"),
                    "South Kesteven District Council",
                    ("Nicola Greaney", "South Kesteven District Council"),
                ),
            ),
            (
                (
                    "Suffolk Mental Health Partnership NHS Trust",
                    ("Naomi Ellenbogen", "Kennedys"),
                ),
                (
                    "Sandwell Metropolitan Borough Council",
                    ("Andrew Stafford QC", "Wragge & Co LLP"),
                    "Hurst & Ors",
                    ("Paul Epstein QC", "Thompsons"),
                    "Arnold & Ors",
                    ("Betsan Criddle", "Thompsons"),
                ),
            ),
        ],
    }

    print(insert_to_database(get_connection(), transform))
