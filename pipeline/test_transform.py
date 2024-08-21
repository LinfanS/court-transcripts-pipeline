"Script that will test the functioning of the transform script"
import pytest 
import unittest
from unittest.mock import MagicMock
from datetime import date
from extract import get_listing_data
from transform import shorten_text_by_tokens, format_date, convert_dict_to_tuple, assemble_data, get_data, get_summary, is_valid_participant, validate_gpt_response

#--cov-report term-missing

@pytest.fixture
def example_data():
    test_url = 'https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=2&from_date_1=2&from_date_2=2003&to_date_0=3&to_date_1=2&to_date_2=2003&party=&judge=&page='
    return get_listing_data(test_url, 1)\

@pytest.fixture
def example_dict():
    return {"verdicts": [], "courts": [], "case_ids": [], "summ": [], "title": [], "date": [], "number": [], "url": [], "v_sum": [], "judges": [], "tags": [], "people": [],}
    

class TestShorterTranscript:

    def test_shorten_text_length_no_change(self):
        assert len(shorten_text_by_tokens('abc123')) == len('abc123')

    def test_shorten_text_length_change(self):
        text = "This is a very long text that should be shortened in the middle"
        assert len(shorten_text_by_tokens(text, 6, 4)) < len(text)
    
    def test_shorten_text_no_text(self):
        assert len(shorten_text_by_tokens('')) == 0


class TestDateFormat:

    def test_date_no_input(self):
        assert format_date(None) == None
    
    def test_date_wrong_input(self):
        assert format_date(3) == None

    def test_date_no_midnight(self):
        assert isinstance(format_date('5 Feb 2022'), date)
    
    def test_date_with_midnight(self):
        assert isinstance(format_date('5 Feb 2022, midnight'), date)

class TestDictConversion:

    def test_dict_converted_to_tuple(self, example_dict):
        example_dict = {
            'first_side' : example_dict,
            'second_side' : example_dict
        }
        assert isinstance(convert_dict_to_tuple(example_dict), tuple)

class TestDataAssembling:

    def test_assemble_data_combines_to_dict(self, example_dict):
        assert isinstance(assemble_data([example_dict, example_dict]), dict)

class TestAllData:

    def test_all(self,example_data):
        assert isinstance(get_data(example_data, 1), dict)

class TestParticipants:

    def test_sample_participants(self):
        test = {"MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None},
            "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}}
        assert is_valid_participant(test) == True

    def test_no_participant_no_crash(self):
        test = {None: {"Lawyer name": None}}
        assert is_valid_participant(test) == True

    def test_no_lawyer_no_crash(self):
        test = {"BIOGAS PRODUCTS LIMITED": {None: None}}
        assert is_valid_participant(test) == True
    
    def test_missing_lawyer_value(self):
        test = {"BIOGAS PRODUCTS LIMITED": {"Lawyer name"}}
        assert is_valid_participant(test) == False

    def test_missing_lawyer(self):
        test = {"BIOGAS PRODUCTS LIMITED": "Lawyer name"}
        assert is_valid_participant(test) == False

    def test_missing_lawyer_and_participant(self):
        test = {None: None}
        assert is_valid_participant(test) == False

class TestGPTResponses:

    def test_valid_gpt_response(self, example_dict):
        example_gpt_dict = {
        "verdict": 'My verdict',
        "summary": 'My summary',
        "case_number": 'My case number',
        "verdict_summary": 'My verdict summary',
        "judge": ['Judge A'],
        "tags": ['Tag A'],
        "first_side": {"MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}},
        "second_side": {"SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}}}
        assert validate_gpt_response(example_gpt_dict) == True


class TestGetSummary(unittest.TestCase):
    
    def test_summary(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(usage=MagicMock(
            completion_tokens=5, prompt_tokens=10, total_tokens=15))   

        prompt = "Summarize this conversation"
        transcript = "The conversation was very productive."
        
        summary = get_summary(prompt, transcript)

        assert isinstance(summary.usage.completion_tokens, int)