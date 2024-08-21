"Script that will take the transformed data and load it to the rds"
import pytest
from bs4 import BeautifulSoup
from extract import get_article_data, get_max_page_num, validate_html_data, extract_judgment_data, get_listing_data

#assuming the cases don't not get deleted
class TestGetData:

    @pytest.fixture
    def href(self):
        return '/ewhc/admin/2024/2177'
    
    @pytest.fixture
    def response(self, href):
        return get_article_data(href)
    
    def test_result_type(self, response):
        assert isinstance(response, str)
    
    def test_result_length(self, response):
        assert len(response) == 18951

    def test_actual_result_start_and_end(self, response):
        response_start = 'Neutral Citation Number: [2024] EWHC 2177'
        response_end = '28.For these reasons I refuse the application for a certificate.'
        assert response[:41] == response_start
        assert response[-64:] == response_end

    def test_wrong_href_int(self):
        with pytest.raises(TypeError) as err:
            assert get_article_data(1) == 'can only concatenate str (not "int") to str'
    
    def test_wrong_href_bool(self):
        with pytest.raises(TypeError) as err:
            assert get_article_data(False) == 'can only concatenate str (not "bool") to str'
    
    def test_wrong_href_empty(self):
        with pytest.raises(AttributeError) as err:
            assert get_article_data('') == "'NoneType' object has no attribute 'get_text'"
            #not error for this function but error later ^
    
class TestMaxPage:

    @pytest.fixture
    def url_no_page_number(self):
        return 'https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=1&from_date_1=2&from_date_2=2003&to_date_0=4&to_date_1=5&to_date_2=2006&party=&judge=&page='
    
    @pytest.fixture
    def nonexistent_url(self):
        return 'https://caselaw.nationalarchives.gov.uk/judgment/search?query=&judge=&party=&order=-date&page='
    
    def test_max_page_returns_correct_type_if_url(self, url_no_page_number):
        assert isinstance(get_max_page_num(url_no_page_number), int)
    
    def test_max_page_returns_correct_type_if_wrong_url(self, nonexistent_url):
        assert isinstance(get_max_page_num(nonexistent_url), int)
    
    def test_max_page_currently(self, url_no_page_number):
        #this will always stay the same as I found the amount of cases and oages between two old dates
        assert get_max_page_num(url_no_page_number) == 693

    def test_max_page_wrong_url(self, nonexistent_url):
        assert get_max_page_num(nonexistent_url) == 0

    def test_max_page_if_one_result(self):
        url = 'https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=2&from_date_1=2&from_date_2=2003&to_date_0=3&to_date_1=2&to_date_2=2003&party=&judge=&page='
        assert get_max_page_num(url) == 1

class TestValidateHTML:
    
    def test_valid_data_true(self):
        example_data = {"title": 'My Title',"url": 'My URL',"court": 'My court',"citation": 'My citation',"date": 'My date',"text_raw": 'My text'}
        assert validate_html_data(example_data) == True
    
    def test_valid_data_no_data(self):
        assert validate_html_data({}) == False
    
    def test_valid_data_invalid_format(self):
        example_data = {"title": 'My Title',"url": 'My URL',"court": 'My court',"citation": 'My citation',"date": 1/2/34,"text_raw": 'My text'}
        assert validate_html_data(example_data) == False

class TestListingData:
    
    @pytest.fixture
    def url_one_case_no_page(self):
        return 'https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=2&from_date_1=2&from_date_2=2003&to_date_0=3&to_date_1=2&to_date_2=2003&party=&judge=&page='
    
    @pytest.fixture
    def page_number(self):
        return 1
    
    @pytest.fixture
    def result(self, url_one_case_no_page, page_number):
        return get_listing_data(url_one_case_no_page, page_number)
       
    def test_get_all_data_type(self, result):
        assert isinstance(result, list)
    
    def test_get_all_data_finds_all_cases(self, result):
        assert len(result) == 6
    
    def test_get_all_data_type_in_list(self, result):
        assert isinstance(result[0], dict)

    def test_get_all_data_keys(self, result):
        assert list(result[0].keys()) == ["title", "url", "court", "citation", "date", "text_raw"]
    
    def test_no_double_insertion(self, url_one_case_no_page, page_number, result):
        original = result
        assuming_first_case_already_exists = get_listing_data(url_one_case_no_page, page_number, [result[0]['citation']])
        assert len(assuming_first_case_already_exists) == len(original) - 1

    def test_no_cases_in_url(self):
        new_url = "https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=1&from_date_1=2&from_date_2=2003&to_date_0=2&to_date_1=2&to_date_2=2003&party=&judge=&page="
        assert len(get_listing_data(new_url, 1)) == 0
        
class TestExtractingData:

    @pytest.fixture
    def html_str(self):
        return """<li>\n<span class="judgment-listing__judgment">\n<span>\n<span class="judgment-listing__title">\n<a href="/ewhc/ch/2003/13">Cibc Mellon Trust Company &amp; Ors v Stolzenberg &amp; Ors</a>\n</span>\n<span class="judgment-listing__court">High Court (Chancery Division)</span>\n</span>\n<span>\n<span class="judgment-listing__neutralcitation">[2003] EWHC 13 (Ch)</span>\n<time class="judgment-listing__date" datetime="3 Feb 2003, midnight">03 Feb 2003</time>\n</span>\n</span>\n</li>"""

    @pytest.fixture
    def base_url(self):
        return "https://caselaw.nationalarchives.gov.uk"

    def test_extract_judgment_data_works(self, html_str, base_url):
        soup = BeautifulSoup(html_str, 'html.parser')
        tags = soup.find_all('li')
        assert isinstance(extract_judgment_data(tags[0], base_url, []), dict)