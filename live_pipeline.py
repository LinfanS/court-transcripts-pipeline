from extract import get_listing_data, get_max_page_num
from transform import get_data, assemble_data
from load import get_connection, insert_to_database

LIVE_URL = """https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=50&order=date&query=&from_date_0=3&from_date_1=8&from_date_2=2024&to_date_0=&to_date_1=&to_date_2=&court=uksc&court=ukpc&court=ewca%2Fciv&court=ewca%2Fcrim&court=ewhc%2Fadmin&court=ewhc%2Fadmlty&court=ewhc%2Fch&court=ewhc%2Fcomm&court=ewhc%2Ffam&court=ewhc%2Fipec&court=ewhc%2Fkb&court=ewhc%2Fmercantile&court=ewhc%2Fpat&court=ewhc%2Fscco&court=ewhc%2Ftcc&party=&judge=&page="""


def handler(event: dict, context) -> None:
    count = 0
    max_page_num = get_max_page_num(LIVE_URL)
    for page_num in range(1, max_page_num + 1):
        gpt_response = []
        data = get_listing_data(LIVE_URL, page_num)
        count += len(data)
        for index, _ in enumerate(data):
            gpt_response.append(get_data(data, index))
        table_data = assemble_data(gpt_response)
        conn = get_connection()
        insert_to_database(conn, table_data)
        print(f"Page {page_num} inserted to database, {count} records in total")
    return "Data inserted to database"


if __name__ == "__main__":
    print(handler({}, None))
