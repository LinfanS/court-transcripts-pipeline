from os import getenv
from datetime import datetime, date
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
from ast import literal_eval
import prompts
from extract import get_listing_data


load_dotenv()


def shorten_text_by_tokens(
    text, keep_start_tokens=4000, keep_end_tokens=4000, placeholder="[...]"
):

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


client = OpenAI(api_key=getenv("OPENAI_API_KEY"))


def get_summary(prompt: str, transcript: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.1,
    )
    print(completion.usage)
    return completion


def get_data(html_data: list[dict], index: int) -> dict:
    transcript = html_data[index].get("text_raw")
    shortened_transcript = shorten_text_by_tokens(transcript)
    del html_data[index]["text_raw"]
    user_message = prompts.user_message + shortened_transcript
    gpt_data = literal_eval(
        get_summary(prompts.system_message, user_message).choices[0].message.content
    )
    data = html_data[index] | gpt_data
    return data


def format_date(date_string: str) -> date:
    if not date_string:
        return None
    clean_date_string = date_string.replace(", midnight", "")
    return datetime.strptime(clean_date_string, "%d %b %Y").date()


def convert_dict_to_tuple(data):
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


def assemble_data(data_list: list[dict]):
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

        table_data["tags"].append(tuple(data.get("tags")))
        table_data["judges"].append(tuple(data.get("judge")))
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

    return table_data


if __name__ == "__main__":
    load_dotenv()
    url_no_page_num = """https://caselaw.nationalarchives.gov.uk/judgments/search?to_date_0=11&to_date_1=8&to_date_2=2024&query=&court=uksc&court=ukpc&court=ewca/civ&court=ewca/crim&court=ewhc/admin&court=ewhc/admlty&court=ewhc/ch&court=ewhc/comm&court=ewhc/fam&court=ewhc/ipec&court=ewhc/kb&court=ewhc/mercantile&court=ewhc/pat&court=ewhc/scco&court=ewhc/tcc&judge=&party=&order=date&page="""
    # print(
    #     shorten_text_by_tokens(
    #         get_listing_data(url_no_page_num, 1)[0].get("text_raw"), 2000, 2000
    #     )
    # )
    html_data = get_listing_data(url_no_page_num, 2)
    print(get_data(html_data, 3))
