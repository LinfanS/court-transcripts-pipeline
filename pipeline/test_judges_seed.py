import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from judges_seed import get_judge_rows, get_bench_judges, get_district_judges_magistrates, get_diversity_high_court_judges, get_judge_advocates, get_circuit_district_judges, gather_all_judges


@pytest.fixture
def fake_get_judge_rows():
    return [
        MagicMock(get_text=MagicMock(return_value="Name")),
        MagicMock(get_text=MagicMock(return_value="Judge 1")),
        MagicMock(get_text=MagicMock(return_value="Judge Dredd")),
        MagicMock(get_text=MagicMock(return_value="Judge 2")),
        MagicMock(get_text=MagicMock(return_value="12345")),
        MagicMock(get_text=MagicMock(return_value="Judge 3")),
    ]


@pytest.fixture
def fake_url():
    return "http://example.com"


class TestGetJudgeRows:
    @patch('judges_seed.requests.get')
    def test_get_judge_rows_correct_length(self, mock_get, fake_url):
        mock_response = MagicMock()
        mock_response.content = """
        <html>
        <body>
        <div class="page__content [ flow ]">
            <table>
                <tr><td>Judge A</td></tr>
                <tr><td>Judge B</td></tr>
            </table>
        </div>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        url = fake_url
        rows = get_judge_rows(url)
        assert len(rows) == 2

    @patch('judges_seed.requests.get')
    def test_get_judge_rows_correct_contents(self, mock_get, fake_url):
        mock_response = MagicMock()
        mock_response.content = """
        <html>
        <body>
        <div class="page__content [ flow ]">
            <table>
                <tr><td>Judge A</td></tr>
                <tr><td>Judge B</td></tr>
            </table>
        </div>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        url = fake_url
        rows = get_judge_rows(url)
        row_texts = [row.get_text() for row in rows]
        assert row_texts == ["Judge A", "Judge B"]


class TestGetBenchJudges:
    @patch("judges_seed.get_judge_rows")
    def test_get_bench_judges(self, mock_get_judge_rows, fake_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = fake_get_judge_rows
        url = fake_url
        judges = get_bench_judges(url)

        assert judges == ["Judge 1", "Judge 2", "Judge 3"]

    @patch("judges_seed.get_judge_rows")
    def test_get_bench_judges_empty(self, mock_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = []
        url = fake_url
        judges = get_bench_judges(url)
        assert judges == []


class TestGetDistrictJudgesMagistrates:
    @patch("judges_seed.get_judge_rows")
    def test_get_judge_ad(self, mock_get_judge_rows, fake_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = fake_get_judge_rows
        url = fake_url
        judges = get_district_judges_magistrates(url)
        assert judges == ["Judge 2"]

    @patch("judges_seed.get_judge_rows")
    def test_get_bench_judges_empty(self, mock_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = []
        url = fake_url
        judges = get_district_judges_magistrates(url)
        assert judges == []


class TestGetDiversityHighCourtJudges:
    @patch("judges_seed.get_judge_rows")
    def test_get_diversity_high_court_judges(self, mock_get_judge_rows, fake_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = fake_get_judge_rows
        url = fake_url
        judges = get_diversity_high_court_judges(url)
        assert judges == ["Judge Dredd"]

    @patch("judges_seed.get_judge_rows")
    def test_get_diversity_high_court_judges_empty(self, mock_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = []
        url = fake_url
        judges = get_diversity_high_court_judges(url)
        assert judges == []


class TestGetJudgeAdvocates:
    @patch("judges_seed.get_judge_rows")
    def test_get_judge_advocates(self, mock_get_judge_rows, fake_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = fake_get_judge_rows
        url = fake_url
        judges = get_judge_advocates(url)
        assert judges == ["Judge Dredd"]

    @patch("judges_seed.get_judge_rows")
    def test_get_judge_advocates_empty(self, mock_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = []
        url = fake_url
        judges = get_judge_advocates(url)
        assert judges == []


class TestGetCircuitDistrictJudges:
    @patch("judges_seed.get_judge_rows")
    def test_get_circuit_district_judges(self, mock_get_judge_rows, fake_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = fake_get_judge_rows
        url = fake_url
        judges = get_circuit_district_judges(url)
        assert judges == ["Judge "]

    @patch("judges_seed.get_judge_rows")
    def test_get_circuit_district_judges_empty(self, mock_get_judge_rows, fake_url):
        mock_get_judge_rows.return_value = []
        url = fake_url
        judges = get_circuit_district_judges(url)
        assert judges == []


class TestGatherAllJudges:
    @patch('judges_seed.get_diversity_high_court_judges')
    @patch('judges_seed.get_bench_judges')
    @patch('judges_seed.get_district_judges_magistrates')
    @patch('judges_seed.get_judge_advocates')
    @patch('judges_seed.get_circuit_district_judges')
    def test_gather_all_judges(self, mock_get_diversity_high_court_judges, mock_get_bench_judges, mock_get_district_judges_magistrates, mock_get_judge_advocates, mock_get_circuit_district_judges):
        mock_get_diversity_high_court_judges.return_value = ["Judge Man"]
        mock_get_bench_judges.return_value = ["Judge Woman"]
        mock_get_district_judges_magistrates.return_value = ["Judge Dredd"]
        mock_get_diversity_high_court_judges.return_value = ["Judge Man"]
        mock_get_diversity_high_court_judges.return_value = ["Judge Man"]
