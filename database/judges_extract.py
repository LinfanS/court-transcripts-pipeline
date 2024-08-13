import requests
from bs4 import BeautifulSoup


def get_judges(url: str) -> list[str]:
    whole_page = requests.get(url)
    soup = BeautifulSoup(whole_page.content, 'html.parser')
    table_contents = soup.find('tbody', class_="govuk-table__body")
    rows = table_contents.find_all("td")
    return [(item.get_text(),) for index, item in enumerate(rows) if index % 2 == 0]


def get_judges_2(url: str) -> list[str]:
    whole_page = requests.get(url)
    soup = BeautifulSoup(whole_page.content, 'html.parser')
    table_contents = soup.find('div', class_="page__content [ flow ]")
    rows = table_contents.find_all("td")
    return [(item.get_text(),) for index, item in enumerate(rows) if index % 2 == 1 and item.get_text() != "Name"]


if __name__ == "__main__":
    high_court_masters = get_judges(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/hc-masters-list/")
    bench_chairs = get_judges_2(
        "https://www.judiciary.uk/about-the-judiciary/who-are-the-judiciary/list-of-members-of-the-judiciary/bench-chairmen-list/")
    print(bench_chairs)
