"Script that will test the functioning of the transform script"
import pytest
import unittest
from unittest.mock import MagicMock, mock_open, patch
from datetime import date
from extract import get_listing_data
from transform import (
    shorten_text_by_tokens,
    format_date,
    convert_dict_to_tuple,
    assemble_data,
    get_data,
    get_summary,
    is_valid_participant,
    validate_gpt_response,
)

# --cov-report term-missing


@pytest.fixture
def example_data():
    test_url = "https://caselaw.nationalarchives.gov.uk/judgments/search?per_page=10&order=-date&query=&from_date_0=2&from_date_1=2&from_date_2=2003&to_date_0=3&to_date_1=2&to_date_2=2003&party=&judge=&page="
    return get_listing_data(test_url, 1)


@pytest.fixture
def example_dict():
    return {
        "verdicts": [],
        "courts": [],
        "case_ids": [],
        "summ": [],
        "title": [],
        "date": [],
        "number": [],
        "url": [],
        "v_sum": [],
        "judges": [],
        "tags": [],
        "people": [],
    }


@pytest.fixture
def example_gpt_dict():
    return {
        "verdict": "My verdict",
        "summary": "My summary",
        "case_number": "My case number",
        "verdict_summary": "My verdict summary",
        "judge": ["Judge A"],
        "tags": ["Tag A"],
        "first_side": {"MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}},
        "second_side": {
            "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
        },
    }


class TestShorterTranscript:

    def test_shorten_text_length_no_change(self):
        assert len(shorten_text_by_tokens("abc123")) == len("abc123")

    def test_shorten_text_length_change(self):
        text = "This is a very long text that should be shortened in the middle"
        assert len(shorten_text_by_tokens(text, 6, 4)) < len(text)

    def test_shorten_text_no_text(self):
        assert len(shorten_text_by_tokens("")) == 0


class TestDateFormat:

    def test_date_no_input(self):
        assert format_date(None) == None

    def test_date_wrong_input(self):
        assert format_date(3) == None

    def test_date_no_midnight(self):
        assert isinstance(format_date("5 Feb 2022"), date)

    def test_date_with_midnight(self):
        assert isinstance(format_date("5 Feb 2022, midnight"), date)


class TestDictConversion:

    def test_dict_converted_to_tuple(self, example_dict):
        example_dict = {"first_side": example_dict, "second_side": example_dict}
        assert isinstance(convert_dict_to_tuple(example_dict), tuple)

    def test_dict_converted_no_claimant(self, example_dict):
        example_dict = {
            "first_side": None,
            "second_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
        }
        assert isinstance(convert_dict_to_tuple(example_dict), tuple)


class TestDataAssembling:

    def test_convert_when_missing_claimant(self):
        example_dict = {
            "first_side": None,
            "second_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
        }
        assert isinstance(convert_dict_to_tuple(example_dict), tuple)


class TestDataAssembling:

    def test_assemble_data_combines_to_dict(self, example_dict):
        assert isinstance(assemble_data([example_dict, example_dict]), dict)

    def test_data_combines_with_response(self, example_gpt_dict):
        assert isinstance(assemble_data([example_gpt_dict]), dict)


class TestDataWriteFile(unittest.TestCase):

    def test_function_writes_to_file_when_is_batch_pipeline(self):
        example_dict = {"verdict": "Guilty"}
        expected_output = str(example_dict) + "\n"

        with patch("builtins.open", mock_open()) as mocked_file:
            assemble_data([example_dict], True)
            mocked_file.assert_called_once_with(
                "invalid_gpt_responses.txt", "a", encoding="utf-8"
            )
            mocked_file().write.assert_called_once_with(expected_output)


class TestAllData:

    @patch("transform.get_summary")
    @patch("transform.shorten_text_by_tokens")
    @patch("transform.prompts")
    def test_get_data(
        self, mock_prompts, mock_shorten_text_by_tokens, mock_get_summary
    ):
        mock_prompts.USER_MESSAGE = "User: "
        mock_prompts.SYSTEM_MESSAGE = "System: "
        mock_shorten_text_by_tokens.return_value = "shortened text"
        mock_summary = MagicMock()
        mock_summary.choices = [
            MagicMock(message=MagicMock(content='{"valid": "string dict"}'))
        ]
        mock_get_summary.return_value = mock_summary
        html_data = [{"text_raw": "Some raw text", "other_key": "other_value"}]
        result = get_data(html_data, 0)

        assert isinstance(result, dict)

    def test_get_data_syntax_error(self):
        html_data = [{"text_raw": "Some raw text"}]
        with patch("transform.get_summary") as mock_get_summary:
            mock_get_summary.return_value.choices[0].message.content = (
                "invalid: string dict}"
            )

            result = get_data(html_data, 0)

            assert result is None


class TestParticipants:

    def test_sample_participants(self):
        test = {
            "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None},
            "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None},
        }
        assert is_valid_participant(test) == True

    def test_no_participant_no_crash(self):
        test = {None: {"Lawyer name": None}}
        assert is_valid_participant(test) == True

    def test_no_lawyer_no_crash(self):
        test = {"BIOGAS PRODUCTS LIMITED": {None: None}}
        assert is_valid_participant(test) == True

    def test_side_name_not_valid_type(self):
        test = {123: {"lawyer": "law_firm"}}
        assert not is_valid_participant(test)

    def test_lawyer_not_valid_type(self):
        test = {"CLIENT": {123: "law_firm"}}
        assert not is_valid_participant(test)

    def test_law_firm_not_valid_type(self):
        test = {"CLIENT": {"LAWYER": 123}}
        assert not is_valid_participant(test)

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

    def test_valid_gpt_response(self, example_gpt_dict):
        example_gpt_dict = {
            "verdict": "My verdict",
            "summary": "My summary",
            "case_number": "My case number",
            "verdict_summary": "My verdict summary",
            "judge": ["Judge A"],
            "tags": ["Tag A"],
            "first_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
            "second_side": {
                "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
            },
        }

        assert validate_gpt_response(example_gpt_dict) == True

    def test_invalid_gpt_response_not_string(self):
        example_gpt_dict = {
            "verdict": 123,
            "summary": "sum",
            "case_number": "My case number",
            "verdict_summary": "My verdict summary",
            "judge": ["Judge A"],
            "tags": ["Tag A"],
            "first_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
            "second_side": {
                "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
            },
        }
        assert validate_gpt_response(example_gpt_dict) == False

    def test_invalid_gpt_response_empty_string(self):
        example_gpt_dict = {
            "verdict": "guilty bad person",
            "summary": "",
            "case_number": "My case number",
            "verdict_summary": "My verdict summary",
            "judge": ["Judge A"],
            "tags": ["Tag A"],
            "first_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
            "second_side": {
                "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
            },
        }
        assert validate_gpt_response(example_gpt_dict) == False

    def test_invalid_gpt_response_empty_list(self):
        example_gpt_dict = {
            "verdict": "guilty bad person",
            "summary": "sum",
            "case_number": "My case number",
            "verdict_summary": "My verdict summary",
            "judge": [],
            "tags": [],
            "first_side": {
                "MICHAEL WILSON & PARTNERS LIMITED": {"David Holland QC": None}
            },
            "second_side": {
                "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
            },
        }
        assert validate_gpt_response(example_gpt_dict) == False

    def test_invalid_gpt_response_invalid_participant(self):
        example_gpt_dict = {
            "verdict": "guilty bad person",
            "summary": "sum",
            "case_number": "My case number",
            "verdict_summary": "My verdict summary",
            "judge": ["Judge A"],
            "tags": ["Tag A"],
            "first_side": {"MICHAEL WILSON & PARTNERS LIMITED": {"Only one term"}},
            "second_side": {
                "SOME OTHER WILSON & PARTNERS LIMITED": {"James Holland QC": None}
            },
        }
        assert validate_gpt_response(example_gpt_dict) == False


class TestGetSummary(unittest.TestCase):

    @patch("transform.OpenAI")
    def test_summary(self, MockOpenAI):
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = MagicMock(
            usage=MagicMock(completion_tokens=5, prompt_tokens=10, total_tokens=15)
        )

        prompt = "Summarize this conversation"
        transcript = "The conversation was very productive."

        summary = get_summary(prompt, transcript)

        assert isinstance(summary.usage.completion_tokens, int)
