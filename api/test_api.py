from fastapi.testclient import TestClient
from unittest.mock import patch, ANY, call
from api import (
    app,
    execute_courts_query,
    execute_judges_query,
    execute_lawyers_query,
    execute_law_firms_query,
    execute_tags_query,
    execute_participants_query,
    execute_court_cases_query,
    Court,
    Judge,
    Lawyer,
    LawFirm,
    Tag,
    ParticipantAssignment,
    CourtCase,
)

client = TestClient(app)


@patch("api.get_db")
def test_read_courts_status_ok(mock_get_db):
    with patch("api.execute_courts_query") as mock_execute:
        mock_execute.return_value = [{"court_name": "High Court"}]
        response = client.get("/courts")
        assert response.status_code == 200


@patch("api.get_db")
def test_read_courts_status_output(mock_get_db):
    with patch("api.execute_courts_query") as mock_execute:
        mock_execute.return_value = [{"court_name": "High Court"}]
        response = client.get("/courts")
        assert response.json() == [{"court_name": "High Court"}]


@patch("api.get_db")
def test_read_judges(mock_get_db):
    with patch("api.execute_judges_query") as mock_execute:
        mock_execute.return_value = [{"judge_name": "John Doe"}]
        response = client.get("/judges/")
        assert response.status_code == 200
        assert response.json() == [{"judge_name": "John Doe"}]


@patch("api.get_db")
def test_read_lawyers(mock_get_db):
    with patch("api.execute_lawyers_query") as mock_execute:
        mock_execute.return_value = [
            {"lawyer_name": "Jane Doe", "law_firm": {"law_firm_name": "Doe Law Firm"}}
        ]
        response = client.get("/lawyers/")
        assert response.status_code == 200
        assert response.json() == [
            {"lawyer_name": "Jane Doe", "law_firm": {"law_firm_name": "Doe Law Firm"}}
        ]


@patch("api.get_db")
def test_read_law_firms(mock_get_db):
    with patch("api.execute_law_firms_query") as mock_execute:
        mock_execute.return_value = [{"law_firm_name": "Doe Law Firm"}]
        response = client.get("/law_firms/")
        assert response.status_code == 200
        assert response.json() == [{"law_firm_name": "Doe Law Firm"}]


@patch("api.get_db")
def test_read_participants(mock_get_db):
    with patch("api.execute_participants_query") as mock_execute:
        example_participant = [
            {
                "court_case_id": "[2020] EWHC 4 (TCC)",
                "is_defendant": False,
                "participant_name": "VVB M&E Group Limited",
                "lawyer_name": "Justin Mort QC",
                "law_firm_name": "Lewis Silkin LLP",
            }
        ]
        mock_execute.return_value = example_participant
        response = client.get("/participants/")
        assert response.status_code == 200
        assert response.json() == example_participant


@patch("api.get_db")
def test_read_tags(mock_get_db):
    with patch("api.execute_tags_query") as mock_execute:
        mock_execute.return_value = [{"tag_name": "Important"}]
        response = client.get("/tags/")
        assert response.status_code == 200
        assert response.json() == [{"tag_name": "Important"}]


@patch("api.get_db")
def test_read_verdicts(mock_get_db):
    with patch("api.execute_verdicts_query") as mock_execute:
        mock_execute.return_value = [{"verdict": "Guilty"}]
        response = client.get("/verdicts/")
        assert response.status_code == 200
        assert response.json() == [{"verdict": "Guilty"}]


@patch("api.get_db")
def test_read_court_cases():
    with patch("api.execute_court_cases_query") as mock_execute:

        example_court_case = [
            {
                "court_case_id": "[2020] EWHC 4 (TCC)",
                "summary": "This case involved a dispute over the ownership of materials between the claimants, VVB M&E Group Limited and VVB Engineering (UK) Limited, and the defendant, Optilan (UK) Limited. The court examined the interpretation of Vesting Certificates that purported to transfer ownership of materials related to a subcontract for the Crossrail project. The judge ultimately determined that the Vesting Certificates effectively vested ownership in VVB, leading to a ruling in their favor.",
                "title": "VVB M&E Group Ltd & Anor v Optilan (UK) Ltd",
                "court_date": "2020-01-07",
                "case_number": "HT-2019-BRS-000016",
                "case_url": "https://caselaw.nationalarchives.gov.uk/ewhc/tcc/2020/4",
                "verdict_summary": "The court ruled in favor of VVB, granting them the relief sought regarding the ownership of materials as specified in the Vesting Certificates. Optilan was ordered to make the materials available for collection.",
                "court": {
                    "court_name": "High Court (Technology and Construction Court)"
                },
                "verdict": {"verdict": "Claimant Wins"},
                "tags": [
                    {"tag_name": "Contract"},
                    {"tag_name": "Construction"},
                    {"tag_name": "Ownership"},
                    {"tag_name": "Subcontract"},
                    {"tag_name": "Vesting certificates"},
                    {"tag_name": "Crossrail"},
                    {"tag_name": "Interim payment"},
                    {"tag_name": "Legal representation"},
                    {"tag_name": "Materials dispute"},
                ],
                "judges": [{"judge_name": "Russen"}],
                "participant_assignments": [
                    {
                        "is_defendant": False,
                        "participant_name": "VVB M&E Group Limited",
                        "lawyer_name": "Justin Mort QC",
                        "law_firm_name": "Lewis Silkin LLP",
                    },
                    {
                        "is_defendant": False,
                        "participant_name": "VVB Engineering (UK) Limited",
                        "lawyer_name": "None",
                        "law_firm_name": "None",
                    },
                    {
                        "is_defendant": True,
                        "participant_name": "Optilan (UK) Limited",
                        "lawyer_name": "Marc Lixenberg",
                        "law_firm_name": "Freeths LLP",
                    },
                ],
            }
        ]
        mock_execute.return_value = example_court_case
        response = client.get("/court_cases/")
        assert response.status_code == 200
        assert response.json() == example_court_case


@patch("api.Session")
def test_execute_courts_query_no_search_no_limit(MockSession):

    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.all.return_value = ["court1", "court2"]

    result = execute_courts_query(None, -1, mock_session)

    mock_session.query.assert_called_once_with(Court)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == ["court1", "court2"]


@patch("api.Session")
def test_execute_courts_query_with_search(MockSession):

    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["court1"]

    result = execute_courts_query("search_term", -1, mock_session)

    mock_session.query.assert_called_once_with(Court)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["court1"]


@patch("api.Session")
def test_execute_courts_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["court1", "court2"]

    result = execute_courts_query(None, 2, mock_session)

    mock_session.query.assert_called_once_with(Court)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == ["court1", "court2"]


@patch("api.Session")
def test_execute_courts_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["court1"]

    result = execute_courts_query("search_term", 1, mock_session)

    mock_session.query.assert_called_once_with(Court)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_called_once_with(1)
    assert result == ["court1"]


@patch("api.Session")
def test_execute_judges_query_no_search_no_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.all.return_value = ["judge1", "judge2"]

    result = execute_judges_query(None, -1, mock_session)

    mock_session.query.assert_called_once_with(Judge)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == ["judge1", "judge2"]


@patch("api.Session")
def test_execute_judges_query_with_search(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["judge1"]

    result = execute_judges_query("search_term", -1, mock_session)

    mock_session.query.assert_called_once_with(Judge)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["judge1"]


@patch("api.Session")
def test_execute_judges_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["judge1", "judge2"]

    result = execute_judges_query(None, 2, mock_session)

    mock_session.query.assert_called_once_with(Judge)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == ["judge1", "judge2"]


@patch("api.Session")
def test_execute_judges_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["judge1"]

    result = execute_judges_query("search_term", 1, mock_session)

    mock_session.query.assert_called_once_with(Judge)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_called_once_with(1)
    assert result == ["judge1"]


@patch("api.Session")
def test_execute_lawyers_query_no_search_no_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.all.return_value = [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]

    result = execute_lawyers_query(None, None, -1, mock_session)

    mock_session.query.assert_called_once_with(Lawyer)
    mock_query.options.assert_called_once_with(ANY)
    mock_query.where.assert_not_called()
    mock_query.join.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]


@patch("api.Session")
def test_execute_lawyers_query_with_search(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]

    result = execute_lawyers_query("search_term", None, -1, mock_session)

    mock_session.query.assert_called_once_with(Lawyer)
    mock_query.options.assert_called_once_with(ANY)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.join.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]


@patch("api.Session")
def test_execute_lawyers_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]

    result = execute_lawyers_query(None, None, 2, mock_session)

    mock_session.query.assert_called_once_with(Lawyer)
    mock_query.options.assert_called_once_with(ANY)
    mock_query.where.assert_not_called()
    mock_query.join.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]


@patch("api.Session")
def test_execute_lawyers_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]

    result = execute_lawyers_query("search_term", "law_firm", 1, mock_session)

    mock_session.query.assert_called_once_with(Lawyer)
    mock_query.options.assert_called_once_with(ANY)
    mock_query.where.assert_has_calls([call(ANY), call(ANY)])
    mock_query.join.assert_called_once_with(Lawyer.law_firm)
    mock_query.limit.assert_called_once_with(1)
    assert result == [
        {
            "lawyer_name": "Justin Mort QC",
            "law_firm": {"law_firm_name": "Lewis Silkin LLP"},
        },
        {"lawyer_name": "None", "law_firm": {"law_firm_name": "May LLP"}},
    ]


@patch("api.Session")
def test_execute_law_firms_query_no_search_no_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.all.return_value = ["law_firm1", "law_firm2"]

    result = execute_law_firms_query(None, -1, mock_session)

    mock_session.query.assert_called_once_with(LawFirm)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == ["law_firm1", "law_firm2"]


@patch("api.Session")
def test_execute_law_firms_query_with_search(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["law_firm1"]

    result = execute_law_firms_query("search_term", -1, mock_session)

    mock_session.query.assert_called_once_with(LawFirm)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["law_firm1"]


@patch("api.Session")
def test_execute_law_firms_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["law_firm1", "law_firm2"]

    result = execute_law_firms_query(None, 2, mock_session)

    mock_session.query.assert_called_once_with(LawFirm)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == ["law_firm1", "law_firm2"]


@patch("api.Session")
def test_execute_law_firms_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["law_firm1"]

    result = execute_law_firms_query("search_term", 1, mock_session)

    mock_session.query.assert_called_once_with(LawFirm)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_called_once_with(1)
    assert result == ["law_firm1"]


@patch("api.Session")
def test_execute_tags_query_no_search_no_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.all.return_value = ["tag1", "tag2"]

    result = execute_tags_query(None, -1, mock_session)

    mock_session.query.assert_called_once_with(Tag)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == ["tag1", "tag2"]


@patch("api.Session")
def test_execute_tags_query_with_search(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["tag1"]

    result = execute_tags_query("search_term", -1, mock_session)

    mock_session.query.assert_called_once_with(Tag)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["tag1"]


@patch("api.Session")
def test_execute_tags_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["tag1", "tag2"]

    result = execute_tags_query(None, 2, mock_session)

    mock_session.query.assert_called_once_with(Tag)
    mock_query.where.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == ["tag1", "tag2"]


@patch("api.Session")
def test_execute_tags_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["tag1"]

    result = execute_tags_query("search_term", 1, mock_session)

    mock_session.query.assert_called_once_with(Tag)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_called_once_with(1)
    assert result == ["tag1"]


@patch("api.Session")
def test_execute_participants_query_no_search_no_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.all.return_value = ["participant1", "participant2"]

    result = execute_participants_query(None, None, None, -1, mock_session)

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_not_called()
    mock_query.where.assert_not_called()
    mock_query.limit.assert_not_called()
    assert result == ["participant1", "participant2"]


@patch("api.Session")
def test_execute_participants_query_with_participant(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["participant1"]

    result = execute_participants_query(
        "participant_name", None, None, -1, mock_session
    )

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_called_once_with(ParticipantAssignment.participant)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["participant1"]


@patch("api.Session")
def test_execute_participants_query_with_lawyer(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["participant1"]

    result = execute_participants_query(None, "lawyer_name", None, -1, mock_session)

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_called_once_with(ParticipantAssignment.lawyer)
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["participant1"]


@patch("api.Session")
def test_execute_participants_query_with_law_firm(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.all.return_value = ["participant1"]

    result = execute_participants_query(None, None, "law_firm_name", -1, mock_session)

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_has_calls(
        [call(ParticipantAssignment.lawyer), call(Lawyer.law_firm)]
    )
    mock_query.where.assert_called_once_with(ANY)
    mock_query.limit.assert_not_called()
    assert result == ["participant1"]


@patch("api.Session")
def test_execute_participants_query_with_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["participant1", "participant2"]

    result = execute_participants_query(None, None, None, 2, mock_session)

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_not_called()
    mock_query.where.assert_not_called()
    mock_query.limit.assert_called_once_with(2)
    assert result == ["participant1", "participant2"]


@patch("api.Session")
def test_execute_participants_query_with_search_and_limit(MockSession):
    mock_session = MockSession()
    mock_query = mock_session.query.return_value
    mock_query.options.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = ["participant1"]

    result = execute_participants_query(
        "participant_name", "lawyer_name", "law_firm_name", 1, mock_session
    )

    mock_session.query.assert_called_once_with(ParticipantAssignment)
    mock_query.options.assert_called_once_with(ANY, ANY)
    mock_query.join.assert_has_calls(
        [
            call(ParticipantAssignment.participant),
            call(ParticipantAssignment.lawyer),
        ]
    )

    mock_query.limit.assert_called_once_with(1)
    assert result == ["participant1"]
