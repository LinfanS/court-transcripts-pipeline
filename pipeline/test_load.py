"Script that will test the functioning of the load script"
import pytest
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from psycopg2.extensions import connection
from load import synonym_extractor, replace_synonyms, return_single_ids, return_multiple_ids
from load import get_verdict_mapping, get_court_mapping, get_tag_mapping, get_judge_mapping, get_law_firm_mapping, get_lawyer_mapping, get_participant_mapping
from load import add_judges, add_tags, add_law_firms, add_participants, add_courts, process_people_data, replace_data, insert_to_database
from load import populate_court_case, populate_judge_assignment, populate_tag_assignment, populate_lawyer, populate_participant_assignment
import nltk
# OOS: test get_connection or reset_schema and test multiple things at once or change to split into multiple functions

nltk.download("wordnet")

@pytest.fixture
def fake_conn():
    return MagicMock()

@pytest.fixture
def fake_cur():
    return MagicMock()

class TestFindSynonyms:
    def test_correct_format(self):
        response = synonym_extractor('hello')
        assert isinstance(response, set)
        assert len(response) != 0
    
    def test_possible_output(self):
        response = synonym_extractor('Achieve')
        assert 'Accomplish' in response
    
    def test_wrong_format_empty(self):
        response = synonym_extractor('')
        assert len(response) == 0
    
    def test_wrong_format_int(self):
        response = synonym_extractor(3)
        assert len(response) == 0

    def test_wrong_format_wrong_character(self):
        response = synonym_extractor('@')
        assert len(response) == 0
    
    def test_wrong_format_empty_bool(self):
        response = synonym_extractor(False)
        assert len(response) == 0

    def test_wrong_format_empty_not_a_word(self):
        response = synonym_extractor('asdfghjkl')
        assert len(response) == 0

    def test_multiple_words(self):
        response = synonym_extractor('not happy')
        assert len(response) !=0


class TestRemoveSynonyms:

    @pytest.fixture
    def list_with(self):
        return ['Scarlet', 'Red']

    @pytest.fixture
    def list_without(self):
        return ['Able', 'Unable', 'Red', 'Red']

    def test_synonyms_get_removed(self, list_with):
        response = replace_synonyms(list_with)
        assert len(set(list_with)) > len(set(response))
        assert 'Scarlet' not in response
    
    def test_synonyms_get_replaced(self, list_with):
        assert len(list_with) == len(replace_synonyms(list_with))

    def test_similar_not_synonym_stay(self, list_without):
        response = replace_synonyms(list_without)
        assert len(set(list_without)) == len(set(response))
        assert len(list_without) == len(response)
    
    def test_edge_cases_empty(self):
        assert len(replace_synonyms([''])) == len([''])
    
    def test_edge_cases_int(self):
        assert len(replace_synonyms([3])) == 0

    def test_edge_cases_bool(self):
        assert len(replace_synonyms([False])) == 0
    
    def test_edge_cases_one_word(self):
        assert len(replace_synonyms(['hello'])) == 1


class TestReturnIds:

    @pytest.fixture
    def fake_map(self):
        return {'hello': 1, 'my': 2, 'name': 3, 'is': 4 }
    
    def test_correct_ids_single(self, fake_map):
        s_response = return_single_ids(fake_map, ('hello', 'name', 'my', 'is'))
        assert s_response == (1,3,2,4)

    def test_correct_ids_multiple(self, fake_map):
        m_response = return_multiple_ids(fake_map, (('hello', 'is'),('my',),('hello', 'my', 'name', 'is')))
        assert m_response == ((1,4),(2,),(1,2,3,4))
    
    def test_edge_ids_multiple_one(self, fake_map):
        assert return_multiple_ids(fake_map, (('hello',),)) == ((1,),)
    
    def test_edge_ids_single_empty(self, fake_map):
        assert return_single_ids(fake_map,()) == ()
    
    def test_edge_ids_multiple_empty(self, fake_map):
        assert return_multiple_ids(fake_map,(('',),)) == ((None,),)
    
    def test_incorrect_id_formats_int_single(self, fake_map):
        assert return_single_ids(fake_map, (1,)) == (None,)
    
    def test_incorrect_id_formats_int_multiple(self, fake_map):
        assert return_multiple_ids(fake_map, ((1,),)) == ((None,),)
    
    def test_incorrect_id_formats_bool_single(self, fake_map):
        assert return_single_ids(fake_map, (False,)) == (None,)

    def test_incorrect_id_formats_bool_multiple(self, fake_map):
        assert return_multiple_ids(fake_map, ((False,),)) == ((None,),)
    
    def test_incorrect_id_formats_one_word_single(self, fake_map):
        assert return_single_ids(fake_map, ('goodbye',)) == (None,)

    def test_incorrect_id_formats_one_word_multiple(self, fake_map):
        assert return_multiple_ids(fake_map, (('goodbye',),)) == ((None,),)


class TestGetMapping:

    def test_verdict_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'verdict':'guilty', 'verdict_id':1}]
        assert get_verdict_mapping(fake_conn) == {'guilty':1}
        assert fake_cur.execute.call_count == 1
    
    def test_court_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'court_name':'high court', 'court_id':1}]
        assert get_court_mapping(fake_conn) == {'high court':1}
        assert fake_cur.execute.call_count == 1

    def test_judge_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'judge_name':'John Doe', 'judge_id':1}]
        assert get_judge_mapping(fake_conn) == {'John Doe':1}
        assert fake_cur.execute.call_count == 1
    
    def test_tag_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'tag_name':'breach', 'tag_id':1}]
        assert get_tag_mapping(fake_conn) == {'breach':1}
        assert fake_cur.execute.call_count == 1

    def test_law_firm_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'law_firm_name':'Solicitors XYZ', 'law_firm_id':1}]
        assert get_law_firm_mapping(fake_conn) == {'Solicitors XYZ':1}
        assert fake_cur.execute.call_count == 1
    
    def test_lawyer_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'lawyer_name':'Jane Smith', 'lawyer_id':1}]
        assert get_lawyer_mapping(fake_conn) == {'Jane Smith':1}
        assert fake_cur.execute.call_count == 1

    def test_lawyer_mapping(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.fetchall.return_value = [{'participant_name':'Sigma Labs', 'participant_id':1}]
        assert get_participant_mapping(fake_conn) == {'Sigma Labs':1}
        assert fake_cur.execute.call_count == 1


class TestInsertions(unittest.TestCase):

    @patch("load.execute_values")
    def test_adding_judges(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        judge_list = [("Judge1",), ("Judge2",), ("Judge3",)]
        result = add_judges(mock_conn, judge_list)
        query = """INSERT INTO judge(judge_name) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, judge_list)
        mock_conn.commit.assert_called_once()
        assert len(result) == len(judge_list)

    @patch("load.execute_values")
    def test_adding_tags(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        tags_list = [("Tag1",), ("Tag2",), ("Tag3",)]
        add_tags(mock_conn, tags_list)
        query = """INSERT INTO tag(tag_name) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, tags_list)
        mock_conn.commit.assert_called_once()
    
    @patch("load.execute_values")
    def test_adding_law_firms(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        firms_list = [("Firm1",), ("Firm2",), ("Firm3",)]
        add_law_firms(mock_conn, firms_list)
        query = """INSERT INTO law_firm(law_firm_name) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, firms_list)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_adding_participants(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        participants_list = [("Participant1",), ("Participant2",), ("Participant3",)]
        add_participants(mock_conn, participants_list)
        query = """INSERT INTO participant(participant_name) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, participants_list)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_adding_courts(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        courts_list = [("Court1",), ("Court2",), ("Court3",)]
        add_courts(mock_conn, courts_list)
        query = """INSERT INTO court(court_name) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, courts_list)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_populating_court_cases(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        a = (('[2003]',),)
        b = (('he died',),)
        c = ((1,),)
        d = (('MM v TF',),)
        e = (('08/07/05',),)
        f = (('2003',),)
        g = (('https',),)
        h = (('ABC123',),)
        i = (('guilty',),)
        matched = []
        for j, value in enumerate(a):
            matched.append((value,b[j],c[j],d[j],e[j],f[j],g[j],h[j],i[j]))
        to_insert = (a,b,c,d,e,f,g,h,i)
        populate_court_case(mock_conn,*to_insert)
        query = """INSERT INTO court_case(court_case_id, summary, verdict_id, title, court_date, case_number, case_url, court_id, verdict_summary) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, matched)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_populate_judge_assignment(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        a = '[2003]'
        b = (1,)
        matched = []
        for item in b:
            matched.append((a, item))
        to_insert = (a,b)
        populate_judge_assignment(mock_conn,*to_insert)
        query = """INSERT INTO judge_assignment(court_case_id, judge_id) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, matched)
        mock_conn.commit.assert_called_once()
    
    @patch("load.execute_values")
    def test_populate_tag_assignment(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        a = 1
        b = (1,)
        matched = []
        for item in b:
            matched.append((a, item))
        to_insert = (a,b)
        populate_tag_assignment(mock_conn,*to_insert)
        query = """INSERT INTO tag_assignment(court_case_id, tag_id) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, matched)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_populate_lawyer_assignment(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        a = ['John Smith']
        b = [1]
        matched = []
        for i, value in enumerate(a):
            matched.append((value, b[i]))
        to_insert = (a,b)
        populate_lawyer(mock_conn,*to_insert)
        query = """INSERT INTO lawyer(lawyer_name, law_firm_id) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, matched)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_populate_participant_assignment(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        a = [((1,(1,1)),(2,(2,2),3,(3,3)),)]
        matched = []
        for case in a:
            for people in case:
                for person in people:
                    matched.append(person)
        populate_participant_assignment(mock_conn,a)
        query = """INSERT INTO participant_assignment(court_case_id, participant_id, lawyer_id, is_defendant) VALUES %s ON CONFLICT DO NOTHING;"""
        mock_execute_values.assert_called_once_with(mock_cursor, query, matched)
        mock_conn.commit.assert_called_once()

    @patch("load.execute_values")
    def test_all_data_insertion(self, mock_execute_values):
        mock_conn = MagicMock(spec=connection)
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        example_data =  {
        "verdicts": ["Dismissed", "Dismissed"],
        "courts": ["High Court (Administrative Court)","Court of Appeal (Civil Division)"],
        "case_ids": ["[2009] EWHC 719 (Admin)", "[2009] EWCA Civ 309"],
        "summ": ["This case involved a judicial review application by the Stamford Chamber of Trade and Commerce and F H Gilman & Co against the Secretary of State for Communities and Local Government and South Kesteven District Council. The claimants challenged the decision not to save Policy T1 of the Local Plan, which safeguarded a proposed road scheme. The court found that the decision was rational and did not require public consultation, leading to the dismissal of the claim.",
                 "This case involved appeals from the Employment Appeal Tribunal regarding equal pay claims made by employees against their employers, Suffolk Mental Health Partnership NHS Trust and Sandwell Metropolitan Borough Council. The central issue was whether the claimants had properly followed the statutory grievance procedures outlined in the Employment Act 2002. The court found that the claimants had indeed complied with the necessary requirements, allowing their claims to be heard despite the employers' objections."],
        "title": ["Stamford Chamber of Trade & Commerce, R (on the application of) v The Secretary of State for Communities and Local Government",
                  "Suffolk Mental Health Partnership NHS Trust v Hurst & Ors"],
        "date": [datetime(2009, 4, 7).date(), datetime(2009, 4, 7).date()],
        "number": ["CO/10442/2007", "A2/2008/2870 & A2/2008/2877"],
        "url": ["https://caselaw.nationalarchives.gov.uk/ewhc/admin/2009/719","https://caselaw.nationalarchives.gov.uk/ewca/civ/2009/309"],
        "v_sum": ["The court dismissed the claim for judicial review, concluding that the Secretary of State's decision not to save Policy T1 of the Local Plan was rational and lawful, and that there was no legitimate expectation for public consultation prior to this decision.",
                  "The court upheld the Employment Appeal Tribunal's decision that the claimants had complied with the statutory grievance procedures under the Employment Act 2002, allowing their equal pay claims to proceed."],
        "judges": [("Rabinder Singh",),("Lord Justice Pill", "Lord Justice Wall", "Lord Justice Etherton")],
        "tags": [("judicial review","planning policy","local government","public consultation","transportation","legitimate expectation","development plan","administrative law","court ruling"),
                 ("equal pay","employment law","grievance procedures","tribunal","NHS","discrimination","collective claims","jurisdiction","statutory compliance")],
        "people": [
            (("The Queen",("Michael Bedford", "Matthew Arnold Baldwin"),"Stamford Chamber of Trade and Commerce",("Michael Bedford", "Matthew Arnold Baldwin")),
            ("F H Gilman & Co",("John Litton", "Treasury Solicitor"),"The Secretary of State for Communities and Local Government",("John Litton", "Treasury Solicitor"),"South Kesteven District Council",("Nicola Greaney", "South Kesteven District Council"))),
        (("Suffolk Mental Health Partnership NHS Trust",("Naomi Ellenbogen", "Kennedys")),
         ("Sandwell Metropolitan Borough Council",("Andrew Stafford QC", "Wragge & Co LLP"),"Hurst & Ors",("Paul Epstein QC", "Thompsons"),"Arnold & Ors",("Betsan Criddle", "Thompsons"))),
        ]}
        result = insert_to_database(mock_conn, example_data)
        assert result == "all files have been uploaded successfully"


class TestDataProcessing:

    def test_people_data_processing(self):
        people = [(('Accusant',('Lawyer','Law Firm')),('Defendor',('Lawyer2','Firm2'),'Defendor2',('Lawyer3','Firm3')))]
        result = process_people_data(people)
        assert len(result) == 3
        assert len(result[0]) == 2
        assert len(result[1]) == 2
        assert len(result[2]) == 2
        assert result[0][0] == [False, True, True]
        assert result[0][1] == ['Lawyer', 'Lawyer2', 'Lawyer3']
        assert result[1][0] == [('Law Firm',), ('Firm2',), ('Firm3',)]
        assert result[1][1] == ['Law Firm','Firm2','Firm3']
        assert result[2][0] == [('Accusant',), ('Defendor',), ('Defendor2',)]
        assert result[2][1] == ['Accusant','Defendor','Defendor2']

    def test_empty_data_processing(self):
        people = [(('',('','')),('',('','')))]
        result = process_people_data(people)
        assert len(result) == 3
        assert result[0][0] == [False, True]

    def test_invalid_data_processing(self):
        result = process_people_data([]) #empty
        assert len(result) == 3
        assert len(result[0][0]) == 0
        result = process_people_data([(('Accusant',('Lawyer','Law Firm')),)]) #no defendant
        #note - if no defendant, should just be empty but still exist
        assert len(result) == 3
        assert len(result[0][0]) != 2

    def test_data_replacement(self):
        unmatched = [('Judge1','Judge2')]
        matched = [('Judge3',),('Judge4',)]
        result = replace_data(unmatched, matched)
        assert (result) == [('Judge3','Judge4')]
        assert len(*result) == len(matched)
        assert len(result) == len(unmatched)

    def test_different_format_replacement(self):
        unmatched = [('Judge1','Judge2'), ('Judge3',)]
        matched = [('Judge4',),('Judge5',), ('Judge6',)]
        result = replace_data(unmatched, matched)
        assert (result) == [('Judge4', 'Judge5'), ('Judge6',)]
        assert len(result) == len(unmatched)
    
    def test_empty_data_replacement(self):
        unmatched = [tuple()]
        matched = [('Judge4',),('Judge5',), ('Judge6',)]
        result = replace_data(unmatched, matched)
        assert len(*result) == 0
    
    def test_wrong_length_replacement(self):
        unmatched = [('Judge1', 'Judge2')]
        matched = [('Judge4',)]
        with pytest.raises(IndexError) as err:
            assert replace_data(unmatched, matched) == """the amount of judges in 'unmatched' does not match the amount of 
                         judges in 'matched' so they cannot be matched"""
