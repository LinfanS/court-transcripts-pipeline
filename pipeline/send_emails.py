from boto3 import client
from os import getenv
from dotenv import load_dotenv


def get_sns_client() -> client:
    """
    Returns an AWS client used for SNS
    """
    return client("sns",

                  region_name="eu-west-2",

                  aws_access_key_id=getenv("ACCESS_KEY"),

                  aws_secret_access_key=getenv("SECRET_ACCESS_KEY"))


def rename_courts(courts: list[str]) -> list[str]:
    """
    Renames the courts to match the topic names on AWS SNS
    """
    topic_names = []
    for court in courts:
        name = ""
        name_parts = court.split(" ")
        new_name = "-".join(name_parts)
        for letter in new_name:
            if letter.isalpha() or letter == "-":
                name += letter
        topic_names.append(f"c12-courts-{name}")
    return topic_names


def send_emails(table_data: dict[list], client) -> None:
    """
    Sends emails to subscribers of the courts being uploaded
    """
    uploading_courts = rename_courts(table_data["courts"])
    for topic_arn in client.list_topics()["Topics"]:
        arn_parts = topic_arn['TopicArn'].split(":")
        topic = arn_parts[-1]
        if topic in uploading_courts:
            court = topic.replace("-", " ")
            court_name = court[11:]
            client.publish(TopicArn=topic_arn["TopicArn"],
                           Message=f"A new case has been uploaded from the {
                court_name}",
                Subject=f"New case(s) uploaded")


if __name__ == "__main__":
    load_dotenv()
    sns = get_sns_client()
    topic_names = rename_courts(
        ["High Court (Commercial Court)", 'High Court (Circuit Commercial Court)'])
    send_emails({"courts": ["High Court (Commercial Court)",
                'High Court (Circuit Commercial Court)']}, sns)
