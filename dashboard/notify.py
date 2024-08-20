from boto3 import client
from os import getenv
from dotenv import load_dotenv


def get_sns_client():

    return client("sns",

                  region_name="eu-west-2",

                  aws_access_key_id=getenv("ACCESS_KEY"),

                  aws_secret_access_key=getenv("SECRET_ACCESS_KEY"))


def create_or_find_topic(client, subscription: str) -> str:
    all_topics = client.list_topics()
    for topic_arn in all_topics["Topics"]:
        arn_parts = topic_arn['TopicArn'].split(":")
        topic = arn_parts[-1]
        if topic == subscription:
            return topic_arn["TopicArn"]
    new_topic = client.create_topic(Name=subscription)
    return new_topic["TopicArn"]


def create_email_subscription(client, email: str, topic_arn: str) -> str:
    subscription = client.subscribe(
        TopicArn=topic_arn, Protocol="email", Endpoint=email)
    return subscription["SubscriptionArn"]


def sub_to_topics(courts: list[str], client, email: str):
    for court in courts:
        name = ""
        name_parts = court.split(" ")
        new_name = "-".join(name_parts)
        for letter in new_name:
            if letter.isalpha() or letter == "-":
                name += letter
        topic_name = f"c12-courts-{name}"
        topic_arn = create_or_find_topic(client, topic_name)
        create_email_subscription(client, email, topic_arn)


if __name__ == "__main__":
    load_dotenv()
    sns = get_sns_client()
    # topic_arn = create_or_find_topic(sns, "c12-courts-test")
    # sub = create_email_subscription(
    #     sns, "trainee.miles.drabwell@sigmalabs.co.uk", topic_arn)
    # sub_to_topics(["High Court (King's Bench Division)",
    #               'High Court (Circuit Commercial Court)'], sns, "milesdrabwell@gmail.com")
