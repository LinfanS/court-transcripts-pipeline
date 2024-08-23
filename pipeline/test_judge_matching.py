import pytest
from unittest.mock import MagicMock, patch
from judge_matching import get_judges, standardise_judge_name, match_judge


class TestGetJudges:
    def test_get_judges_returns_list_of_strings(self):
        fake_conn = MagicMock()
        fake_cursor = MagicMock()

        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

        fake_cursor.fetchall.return_value = [
            {"judge_name": "Judge Jez"},
            {"judge_name": "Judge Betty"},
            {"judge_name": "Judge Cranium"},
        ]

        result = get_judges(fake_conn)

        assert isinstance(result, list)
        assert all(isinstance(name, str) for name in result)

    def test_get_judges_returns_correct(self):
        fake_conn = MagicMock()
        fake_cursor = MagicMock()

        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

        fake_cursor.fetchall.return_value = [
            {"judge_name": "Judge Jez"},
            {"judge_name": "Judge Betty"},
            {"judge_name": "Judge Cranium"},
        ]

        result = get_judges(fake_conn)

        assert result == ["Judge Jez", "Judge Betty", "Judge Cranium"]


class TestStandardiseJudgeNames:
    def test_standardise_judge_names_works(self):
        name = "Judge James CBE"
        assert standardise_judge_name(
            name) == "James"


class TestMatchJudge:
    def test_match_judge_correct(self):
        result = match_judge("Justice James", ["James", "Terrence"])
        assert result == "James"

    def test_match_judge_no_match(self):
        result = match_judge("John", ["James", "Terrence"])
        assert result == "John"

    def test_match_judge_no_match_standardised(self):
        result = match_judge("Judge John", ["James", "Terrence"])
        assert result == "John"
