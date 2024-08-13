from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import prompts
from extract import get_listing_data

enc = tiktoken.encoding_for_model("gpt-4o-mini")

text = get_listing_data(2)[0].get("text_raw")
tokens = enc.encode(text)

load_dotenv()


client = OpenAI(api_key=getenv("OPENAI_API_KEY"))

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
    transcript = get_listing_data(3)[1].get("text_raw")
    user_message = prompts.user_message + transcript
    response = get_summary(prompts.system_message, user_message)
    output = response.choices[0].message.content
    print(output)
    with open("gpt_out.md", "w") as file:
        file.write(output)
    print(response.usage)
