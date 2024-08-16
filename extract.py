"""Python script to read HTML of case law website and obtain available data for each case"""

from bs4 import BeautifulSoup
import requests


def get_article_data(href: str) -> str:
    """Returns text contents of a single case by returning article tag contents"""

    base_url = "https://caselaw.nationalarchives.gov.uk"
    page = requests.get(base_url + href)

    soup = BeautifulSoup(page.content, "html.parser")
    article_only = soup.article

    text_raw = article_only.get_text()
    return text_raw


def get_max_page_num(url_no_page_num: str) -> int:
    """Returns the maximum page number available for a given URL"""
    url = url_no_page_num + "1"

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    pagination = soup.find("nav", {"aria-label": "Results pagination"})
    if not pagination:
        return 0
    page_links = pagination.find_all("a", class_="pagination__page-link")

    page_numbers = [
        int(link.get_text(strip=True).replace("Page", "").strip())
        for link in page_links
        if link.get_text(strip=True).startswith("Page")
    ]

    if not page_numbers:
        return 1

    return max(page_numbers)


def validate_html_data(data: dict) -> bool:
    """Validates the data extracted from the HTML"""

    required_keys = ["title", "url", "court", "citation", "date", "text_raw"]

    for key in required_keys:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            return False

    return True


def get_listing_data(
    url_no_page_num: str, page_num: int, already_loaded=None
) -> list[dict]:
    """Returns a list of dictionaries with the data for a given page number sorting by oldest"""

    url = url_no_page_num + str(page_num)
    base_url = "https://caselaw.nationalarchives.gov.uk"
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")

    ul_tag = soup.find("ul", class_="judgment-listing__list")

    if not ul_tag:
        return []
    list_items = ul_tag.find_all("li")

    judgments = []
    if not already_loaded:
        already_loaded = []

    for item in list_items:
        title_tag = item.find("span", class_="judgment-listing__title")
        court_tag = item.find("span", class_="judgment-listing__court")
        citation_tag = item.find("span", class_="judgment-listing__neutralcitation")
        date_tag = item.find("time", class_="judgment-listing__date")

        title = title_tag.get_text(strip=True) if title_tag else None
        href = title_tag.find("a")["href"] if title_tag and title_tag.find("a") else ""
        court = court_tag.get_text(strip=True) if court_tag else None
        citation = citation_tag.get_text(strip=True) if citation_tag else None
        date = date_tag.get("datetime") if date_tag else None

        if citation not in already_loaded:

            html_data = {
                "title": title,
                "url": base_url + href,
                "court": court,
                "citation": citation,
                "date": date,
                "text_raw": get_article_data(href),
            }
            if validate_html_data(html_data):
                judgments.append(html_data)

    return judgments


if __name__ == "__main__":
    # url_no_page_num = """https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=50&order=date&query=&from_date_0=12&from_date_1=8&from_date_2=2024&to_date_0=&to_date_1=&to_date_2=&court=uksc&court=ukpc&court=ewca%2Fciv&court=ewca%2Fcrim&court=ewhc%2Fadmin&court=ewhc%2Fadmlty&court=ewhc%2Fch&court=ewhc%2Fcomm&court=ewhc%2Ffam&court=ewhc%2Fipec&court=ewhc%2Fkb&court=ewhc%2Fmercantile&court=ewhc%2Fpat&court=ewhc%2Fscco&court=ewhc%2Ftcc&party=&judge=&page="""
    url_no_page_num = """https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=&from_date_1=&from_date_2=&to_date_0=&to_date_1=&to_date_2=&court=ewhc%2Fipec&party=&judge=&page="""
    print(get_max_page_num(url_no_page_num))

    print([d.get("url") for d in get_listing_data(url_no_page_num, 5)])
