"""Script that will take the transformed data and load it to the rds"""

import datetime
from os import environ
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import connection
from dotenv import load_dotenv
import nltk
from nltk.corpus import wordnet
from Levenshtein import jaro_winkler
from judge_matching import match_judge, get_judges
from judges_seed import seed_judges


def synonym_extractor(phrase: str) -> set[str]:
    """Uses the wordnet module from the nltk library to find synonyms of a word"""
    if not isinstance(phrase, str):
        return set()
    synonyms = []
    for word in phrase.split(" "):
        for syn in wordnet.synsets(word):
            for l in syn.lemmas():
                synonyms.append(l.name())
        synonyms = {word.capitalize() for word in synonyms}
        if word in synonyms:
            synonyms.remove(str(word))
        synonyms = list(synonyms)
    return set(synonyms)


def replace_word_in_list(words: list[str], old_word: str, new_word: str) -> list[str]:
    """Replaces all occurrences of old_word with new_word in the list."""
    return [new_word if word == old_word else word for word in words]


def replace_synonyms(words: list[str]) -> list[str]:
    """Replaces any synonym in a list of words with its original word.
    Based on the above synonym function or if it has a high jaro winkler match"""
    for word in words:  # replace any synonyms
        synonyms = synonym_extractor(word)
        if synonyms:
            for syn in synonyms:
                if str(syn) in set(words):
                    words = replace_word_in_list(words, word, syn)

        for word2 in words:  # replace any too-similar words
            if not isinstance(word2, str):
                words.remove(word2)
            if not word == word2:
                jw = jaro_winkler(word, word2)
                if jw > 0.9:
                    words = replace_word_in_list(words, word, word2)
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


def reset_schema_and_seed(conn: connection):
    """running schema to empty the tables (will need re-seeding for judges)"""
    with open("schema.sql", "r", encoding="utf-8") as file:
        code = file.read()
        with conn.cursor() as cur:
            cur.execute(code)
        conn.commit()
    seed_judges()
    print("Schema reset and judges re-seeded")


def return_single_ids(mapping: dict, to_convert: tuple[str]) -> tuple[int]:
    """Based on a dict, will convert values (=keys of the dict) to their corresponding value"""
    to_return = []
    for item in to_convert:
        to_return.append(mapping.get(item))
    return tuple(to_return)


def return_multiple_ids(
    mapping: dict, to_convert: tuple[tuple[str]]
) -> tuple[tuple[int]]:
    """Like above but for when the values to convert are nested"""
    to_return = []
    for case in to_convert:
        group = []
        for item in case:
            group.append(mapping.get(item))
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
    """To map each lawyer (and consequently firm) to its id"""
    with conn.cursor() as cur:
        cur.execute("SELECT lawyer_name, lawyer_id FROM lawyer")
        rows = cur.fetchall()
    return {row["lawyer_name"]: row["lawyer_id"] for row in rows}


def add_judges(conn: connection, all_judges_list: list[tuple[str]]) -> list[tuple[str]]:
    """Adds new judges to the table judge and returns a list of all the ones it was able to match"""
    matched_judges_list = [
        (match_judge(judge_name[0], get_judges(conn)),)
        for judge_name in all_judges_list
    ]
    query = """INSERT INTO judge(judge_name) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, matched_judges_list)
    conn.commit()
    return matched_judges_list


def add_tags(conn: connection, all_tags_list: list[tuple[str]]):
    """Adds new tags to the tag table"""
    query = """INSERT INTO tag(tag_name) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, all_tags_list)
    conn.commit()


def add_law_firms(conn: connection, all_firm_names: list[tuple[str]]):
    """Adds new law firm names to the law_firm table"""
    query = """INSERT INTO law_firm(law_firm_name) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, all_firm_names)
    conn.commit()


def add_participants(conn: connection, all_participant_names: list[tuple[str]]):
    """Adds people's names to the participants table"""
    query = """INSERT INTO participant(participant_name) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, all_participant_names)
    conn.commit()


def add_courts(conn: connection, all_court_names: list[tuple[str]]):
    """Adds new court names to the court table"""
    query = """INSERT INTO court(court_name) VALUES %s ON CONFLICT DO NOTHING;"""
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
):
    # pylint: disable=R0913
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
    query = """INSERT INTO court_case(court_case_id, summary, verdict_id, title, court_date, case_number, case_url, court_id, verdict_summary) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()


def populate_judge_assignment(conn: connection, case_id: int, judge_id: tuple[int]):
    """Populates the judge_assignment table base don case id and judge id"""
    matched = []
    for judge in judge_id:
        matched.append((case_id, judge))
    query = """INSERT INTO judge_assignment(court_case_id, judge_id) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()


def populate_tag_assignment(conn: connection, case_id: int, tags_ids: tuple[int]):
    """Populates the tag assignment table based on a case id and its tag ids"""
    matched = []
    for tag in tags_ids:
        matched.append((case_id, tag))
    query = """INSERT INTO tag_assignment(court_case_id, tag_id) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()


def populate_lawyer(
    conn: connection, all_lawyers: list[str], all_law_firm_ids: list[int]
):
    """Add data to the lawyer table that matches lawyers to their firm"""
    matched = []
    for i, value in enumerate(all_lawyers):
        matched.append((value, all_law_firm_ids[i]))
    query = """INSERT INTO lawyer(lawyer_name, law_firm_id) VALUES %s ON CONFLICT DO NOTHING;"""
    with conn.cursor() as cur:
        execute_values(cur, query, matched)
    conn.commit()


def populate_participant_assignment(
    conn: connection, people_ids: list[tuple[tuple[int]]]
) -> list[tuple[tuple[int] | int]]:
    """Populates the participant_assignment table by linking a case id to its participant(s),
    their lawyer(s) and whether they are defending"""
    query = """INSERT INTO participant_assignment(court_case_id, participant_id, lawyer_id, is_defendant) VALUES %s ON CONFLICT DO NOTHING;"""
    # combine into one
    to_add = []
    for case in people_ids:
        for people in case:
            for person in people:
                to_add.append(person)

    with conn.cursor() as cur:
        execute_values(cur, query, to_add)
    conn.commit()


def process_people_data(people: list[tuple[tuple[str] | str | bool]]) -> list[tuple]:
    """Converting all the information about the people to usable lists based on who they are"""
    lawyer_list, law_firm_list, people_list = ([], []), ([], []), ([], [])
    for case in people:
        for i, side in enumerate(case):
            for j, person in enumerate(side):
                if (j + 1) % 2 == 0:
                    lawyer_list[0].append(bool(i))
                    lawyer_list[1].append(person[0])
                    law_firm_list[0].append((person[1],))
                    law_firm_list[1].append(person[1])
                if (j + 2) % 2 == 0:
                    people_list[0].append((person,))
                    people_list[1].append(person)
    return lawyer_list, law_firm_list, people_list


def replace_data(
    unmatched_judges: list[tuple[str]], matched_judges: list[tuple[str]]
) -> list[tuple[str]]:
    """Updates judges' names if they weren't in the table"""
    result = []
    matched_judge_idx = 0
    for judge_tuple in unmatched_judges:
        new_tuple = tuple(
            matched_judges[matched_judge_idx + i][0] for i in range(len(judge_tuple))
        )
        result.append(new_tuple)
        matched_judge_idx += len(judge_tuple)
    return result


def transform_tags(tags_to_convert: list[tuple[str]]) -> list[tuple[str]]:
    """Replaces all synonyms from tags and returns them in the same format they were inputted"""
    all_tags = []
    for case in tags_to_convert:
        for tag in case:
            all_tags.append(tag)
    temp_tags = replace_synonyms(all_tags)

    reconstructed = []
    i = 0
    for case in tags_to_convert:
        group = []
        for tag in case:
            group.append(temp_tags[i])
            i += 1
        reconstructed.append(tuple(group))
    return reconstructed


def people_id_in_right_format(
    people: list[tuple[tuple[str] | str | bool]],
    c_case_ids: list[int],
    part_ids: list[int],
    law_ids: list[int],
    firm_ids: list[bool],
) -> list[tuple[tuple[int] | int]]:
    """Copies the structure used in 'people' but returns their ids instead
    Will now be in the right format to be inserted"""
    people_ids = []
    i = 0
    j = 0
    for k, case in enumerate(people):  # for every case
        case_to_add = []
        for side in case:  # always two sides so this should always be run twice
            side_to_add = []
            group = []
            for c in range(len((side))):
                if (c + 1) % 2 != 0:  # people
                    group.append(part_ids[i])
                    i += 1
                elif (c + 1) % 2 == 0:  # lawyers
                    group.append(law_ids[j])
                    group.append(firm_ids[j])
                    j += 1
                if len(group) == 3:
                    group.insert(0, c_case_ids[k])
                    side_to_add.append(tuple(group))
                    group = []
            case_to_add.append(tuple(side_to_add))
        people_ids.append(case_to_add)
    return people_ids


def insert_to_database(conn: connection, transformed_data: dict) -> str:
    # pylint: disable=R0914
    """Takes data from the transform, adds them to the database based on mappings created"""

    allowed_verdicts = (
        "Guilty",
        "Not Guilty",
        "Dismissed",
        "Acquitted",
        "Hung Jury",
        "Claimant Wins",
        "Defendant Wins",
        "Settlement",
        "Struck Out",
        "Appeal Dismissed",
        "Appeal Allowed",
        "Other",
    )
    for i, verdict in enumerate(transformed_data["verdicts"]):
        if verdict not in allowed_verdicts:
            transformed_data["verdicts"][i] = "Other"

    verdict_map = get_verdict_mapping(conn)

    add_courts(conn, [(court,) for court in transformed_data["courts"]])
    court_map = get_court_mapping(conn)

    judges = transformed_data["judges"]
    matched_judges_list = add_judges(
        conn, [(judge,) for case in judges for judge in case]
    )
    updated_judge_names = replace_data(judges, matched_judges_list)
    judges_map = get_judge_mapping(conn)

    tags = transform_tags(transformed_data["tags"])
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
    part_assign = people_id_in_right_format(
        transformed_data["people"],
        transformed_data["case_ids"],
        participant_ids,
        lawyer_ids,
        lawyer_list[0],
    )

    populate_participant_assignment(conn, part_assign)
    for i, case_id in enumerate(transformed_data["case_ids"]):
        populate_judge_assignment(conn, case_id, j_ids[i])
        populate_tag_assignment(conn, case_id, tag_ids[i])

    return "all files have been uploaded successfully"


if __name__ == "__main__":
    load_dotenv()
    nltk.download("wordnet")
    transform = {
        "verdicts": ["Dismissed", "Dismissed"],
        "courts": [
            "High Court (Administrative Court)",
            "Court of Appeal (Civil Division)",
        ],
        "case_ids": ["[2009] EWHC 719 (Admin)", "[2009] EWCA Civ 309"],
        "summ": [
            """This case involved a judicial review application by the Stamford Chamber
            of Trade and Commerce and F H Gilman & Co against the Secretary of State for
            Communities and Local Government and South Kesteven District Council. The
            claimants challenged the decision not to save Policy T1 of the Local Plan, which
            safeguarded a proposed road scheme. The court found that the decision was rational
            and did not require public consultation, leading to the dismissal of the claim.""",
            """This case involved appeals from the Employment Appeal Tribunal regarding equal pay
            claims made by employees against their employers, Suffolk Mental Health Partnership NHS
            Trust and Sandwell Metropolitan Borough Council. The central issue was whether the
            claimants had properly followed the statutory grievance procedures outlined in the
            Employment Act 2002. The court found that the claimants had indeed complied with the
            necessary requirements, allowing their claims to be heard despite the employers'
            objections.""",
        ],
        "title": [
            """Stamford Chamber of Trade & Commerce, R (on the application of) v The Secretary of
            State for Communities and Local Government""",
            "Suffolk Mental Health Partnership NHS Trust v Hurst & Ors",
        ],
        "date": [datetime.date(2009, 4, 7), datetime.date(2009, 4, 7)],
        "number": ["CO/10442/2007", "A2/2008/2870 & A2/2008/2877"],
        "url": [
            "https://caselaw.nationalarchives.gov.uk/ewhc/admin/2009/719",
            "https://caselaw.nationalarchives.gov.uk/ewca/civ/2009/309",
        ],
        "v_sum": [
            """The court dismissed the claim for judicial review, concluding that the
                  Secretary of State's decision not to save Policy T1 of the Local Plan was rational
                  and lawful, and that there was no legitimate expectation for public consultation
                  prior to this decision.""",
            """The court upheld the Employment Appeal Tribunal's decision that the claimants had
            complied with the statutory grievance procedures under the Employment Act 2002,
            allowing their equal pay claims to proceed.""",
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
                    None,
                    (None, None),
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
