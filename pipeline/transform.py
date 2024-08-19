"""Python script to transform the data extracted from the National Archives 
website through ChatGPT into a format that can be loaded into a database"""

from os import getenv
from datetime import datetime, date
from string import capwords
import logging
from ast import literal_eval
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
import tiktoken
import prompts
from extract import get_listing_data


load_dotenv()
logger = logging.getLogger("batch_pipeline")
client = OpenAI(api_key=getenv("OPENAI_API_KEY"))


def shorten_text_by_tokens(
    text: str,
    keep_start_tokens: int = 4000,
    keep_end_tokens: int = 4000,
    placeholder: str = "[...]",
) -> str:
    """Shortens court transcript by removing tokens from the middle"""
    encoder = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoder.encode(text)

    if len(tokens) <= keep_start_tokens + keep_end_tokens:
        return text

    start_tokens = tokens[:keep_start_tokens]
    end_tokens = tokens[-keep_end_tokens:]

    start_text = encoder.decode(start_tokens)
    end_text = encoder.decode(end_tokens)

    shortened_text = f"{start_text}{placeholder}{end_text}"

    return shortened_text


def get_summary(prompt: str, transcript: str) -> ChatCompletion:
    """Collect data about the transcript using the GPT-4o-mini model"""
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.1,  # low temperature to ensure the model doesn't diverge from the prompt
    )
    usage = completion.usage
    completion_tokens = getattr(usage, "completion_tokens", 0)
    prompt_tokens = getattr(usage, "prompt_tokens", 0)
    total_tokens = getattr(usage, "total_tokens", 0)
    cost = [completion_tokens, prompt_tokens, total_tokens]
    logger.info("GPT-4o-mini usage cost: %s", cost)
    return completion


def is_valid_participant(data: dict) -> bool:
    """Check if the participant dict is valid"""
    for key, value in data.items():
        if not isinstance(key, (str, type(None))):
            return False
        if not isinstance(value, dict):
            return False
        for sub_key, sub_value in value.items():
            if not isinstance(sub_key, (str, type(None))):
                return False
            if not isinstance(sub_value, (str, type(None))):
                return False

    return True


def validate_gpt_response(data: dict) -> bool:
    """Validates the data shape extracted from the GPT-4o-mini API"""
    expected_keys = {
        "verdict": str,
        "summary": str,
        "case_number": str,
        "verdict_summary": str,
        "judge": list,
        "tags": list,
        "first_side": dict,
        "second_side": dict,
    }

    for key, expected_type in expected_keys.items():
        value = data.get(key)
        if value is None:
            return False
        if not isinstance(value, expected_type):
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        if isinstance(value, dict):
            if not is_valid_participant(value):
                return False

    return True


def get_data(html_data: list[dict], index: int) -> dict:
    """Combines the html data with the GPT-4o-mini data for a single case"""
    transcript = html_data[index].get("text_raw")
    shortened_transcript = shorten_text_by_tokens(transcript)
    del html_data[index]["text_raw"]
    user_message = prompts.USER_MESSAGE + shortened_transcript
    try:
        # converts a dict-like string to a dict
        gpt_data = literal_eval(
            get_summary(prompts.SYSTEM_MESSAGE, user_message).choices[0].message.content
        )
    except (SyntaxError, ValueError):
        return None
    data = html_data[index] | gpt_data
    return data


def format_date(date_string: str) -> date:
    """Converts a date string to a date object"""
    if not date_string:
        return None
    clean_date_string = date_string.replace(", midnight", "")
    return datetime.strptime(clean_date_string, "%d %b %Y").date()


def convert_dict_to_tuple(data: dict) -> tuple:
    """Converts a claimant and defendant data dictionary to a tuple"""
    result = []
    for outer_key, inner_dict in data.items():
        if inner_dict is None:
            result.append((outer_key, (None, None)))
        else:
            inner_key = list(inner_dict.keys())[0]
            inner_value = inner_dict[inner_key]
            result.append((outer_key, (inner_key, inner_value)))
    flattened_result = tuple(item for sublist in result for item in sublist)

    return flattened_result


def assemble_data(data_list: list[dict], is_batch_pipeline: bool = False) -> dict:
    """Formats the combined data from into a single dictionary for load"""
    table_data = {
        "verdicts": [],
        "courts": [],
        "case_ids": [],
        "summ": [],
        "title": [],
        "date": [],
        "number": [],
        "url": [],
        "v_sum": [],
        "judges": [],
        "tags": [],
        "people": [],
    }

    for data in data_list:
        if data is not None:
            if validate_gpt_response(data):

                table_data["tags"].append(
                    tuple((tag.capitalize() for tag in data.get("tags")))
                )
                table_data["judges"].append(
                    tuple((capwords(judge) for judge in data.get("judge")))
                )
                table_data["verdicts"].append(data.get("verdict"))
                table_data["courts"].append(data.get("court"))
                table_data["case_ids"].append(data.get("citation"))
                table_data["summ"].append(data.get("summary"))
                table_data["title"].append(data.get("title"))
                table_data["date"].append(format_date(data.get("date")))
                table_data["number"].append(data.get("case_number"))
                table_data["url"].append(data.get("url"))
                table_data["v_sum"].append(data.get("verdict_summary"))
                table_data["people"].append(
                    (
                        convert_dict_to_tuple(data.get("first_side")),
                        convert_dict_to_tuple(data.get("second_side")),
                    )
                )
            else:
                logger.warning("Invalid GPT response: %s", data)
                if is_batch_pipeline:
                    with open("invalid_gpt_responses.txt", "a", encoding="utf-8") as f:
                        f.write(str(data) + "\n")

    return table_data


if __name__ == "__main__":
    load_dotenv()
    URL_NO_PAGE_NUM = """https://caselaw.nationalarchives.gov.uk/judgments/search?to_date_0=11&to_date_1=8&to_date_2=2024&query=&court=uksc&court=ukpc&court=ewca/civ&court=ewca/crim&court=ewhc/admin&court=ewhc/admlty&court=ewhc/ch&court=ewhc/comm&court=ewhc/fam&court=ewhc/ipec&court=ewhc/kb&court=ewhc/mercantile&court=ewhc/pat&court=ewhc/scco&court=ewhc/tcc&judge=&party=&order=date&page="""
    sample_html_data = get_listing_data(URL_NO_PAGE_NUM, 2)
    print(get_data(sample_html_data, 3))
