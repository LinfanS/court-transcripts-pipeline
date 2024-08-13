"""Python script to read HTML of case law website and obtain available data for each case"""

from bs4 import BeautifulSoup
import requests
import html2text


def get_article_data(href: str) -> tuple[str]:
    """Returns text contents of a single case by returning article tag contents"""
    base_url = "https://caselaw.nationalarchives.gov.uk"
    page = requests.get(base_url + href)

    soup = BeautifulSoup(page.content, "html.parser")
    article_only = soup.article

    text_md = html2text.html2text(article_only.text)

    text_raw = article_only.get_text()
    return text_md, text_raw


def get_listing_data(page_num: int) -> list[dict]:
    """Returns a list of dictionaries with the data for a given page number sorting by oldest"""
    url = f"""https://caselaw.nationalarchives.gov.uk/judgments/
    search?query=&judge=&party=&order=-date&page={page_num}&order=date&per_page=50"""

    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")

    ul_tag = soup.find("ul", class_="judgment-listing__list")
    list_items = ul_tag.find_all("li")

    judgments = []

    for item in list_items:
        title_tag = item.find("span", class_="judgment-listing__title")
        court_tag = item.find("span", class_="judgment-listing__court")
        citation_tag = item.find("span", class_="judgment-listing__neutralcitation")
        date_tag = item.find("time", class_="judgment-listing__date")

        title = title_tag.get_text(strip=True) if title_tag else None
        href = (
            title_tag.find("a")["href"] if title_tag and title_tag.find("a") else None
        )
        court = court_tag.get_text(strip=True) if court_tag else None
        citation = citation_tag.get_text(strip=True) if citation_tag else None
        date = date_tag.get("datetime") if date_tag else None

        judgments.append(
            {
                "title": title,
                "href": href,
                "court": court,
                "citation": citation,
                "date": date,
                "text_md": get_article_data(href)[0],
                "text_raw": get_article_data(href)[1],
            }
        )

    return judgments


if __name__ == "__main__":
    print(get_listing_data(1))
