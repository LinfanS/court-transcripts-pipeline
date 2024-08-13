from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import prompts
from extract import get_listing_data

# enc = tiktoken.encoding_for_model("gpt-4o")

# text = "Hello, world!"
# tokens = enc.encode(text)

# print(tokens)
# print(text)

load_dotenv()


client = OpenAI(api_key=getenv("OPENAI_API_KEY"))


# max_tokens = 1000
summary_topic = "Court Transcript Summary"
system_message = prompts.system_message


def get_summary(prompt: str, transcript: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.3,
    )

    return completion


if __name__ == "__main__":
    load_dotenv()
    transcript = get_listing_data(2)[0].get("text_raw")
    response = get_summary(prompts.system_message, transcript)
    print(response.choices[0].message)
    print(response.usage)
