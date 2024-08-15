import json


def initialise_json(live_start_date):

    log_json = {live_start_date: []}

    file_name = "log.json"

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(log_json, f)


if __name__ == "__main__":
    initialise_json("12-08-2024")
