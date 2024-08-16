"Script that will take the transformed data and load it to the rds"
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call
from load import synonym_extractor, replace_synonyms, return_single_ids, return_multiple_ids
from load import get_verdict_mapping, get_court_mapping, get_tag_mapping, get_judge_mapping, get_law_firm_mapping, get_lawyer_mapping, get_participant_mapping
from load import add_judges, add_tags, add_law_firms, add_participants, add_courts, process_people_data, replace_data, insert_to_database
from load import populate_court_case, populate_judge_assignment, populate_tag_assignment, populate_lawyer, populate_participant_assignment
from psycopg2.extras import execute_values
#TODO: test get_connection or reset_schema

@pytest.fixture
def fake_conn():
    return MagicMock()

# @pytest.fixture
# def fake_conn():
#     mock_conn = MagicMock()
#     mock_cur = MagicMock()
#     mock_cur.connection.encoding = 'utf-8'
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cur
#     return mock_conn

@pytest.fixture
def fake_cur():
    return MagicMock()

# @pytest.fixture
# def fake_cur(fake_conn):
#     return fake_conn.cursor.return_value.__enter__.return_value


class TestFindSynonyms:
    def test_correct_format(self):
        response = synonym_extractor('hello')
        assert isinstance(response, set)
        assert len(response) != 0
    
    def test_possible_output(self):
        response = synonym_extractor('Achieve')
        assert 'Accomplish' in response
    
    def test_wrong_format(self):
        #TODO: how to test multiple at once
        response = synonym_extractor('')
        assert len(response) == 0
        response = synonym_extractor(3)
        assert len(response) == 0
        response = synonym_extractor('@')
        assert len(response) == 0
        response = synonym_extractor(False)
        assert len(response) == 0
        response = synonym_extractor('asdfghjkl')
        assert len(response) == 0

    def test_multiple_words(self):
        response = synonym_extractor('not happy')
        assert len(response) !=0

class TestRemoveSynonyms:
    #note - all words to check are capitalised as we transform all tags to be capitalised
    #(this would also work if not capitalised as long as it's consistent)
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
    
    def test_edge_cases(self):
        assert len(replace_synonyms([''])) == len([''])
        assert len(replace_synonyms([3])) == 0
        assert len(replace_synonyms([False])) == 0
        assert len(replace_synonyms(['hello'])) == 1

class TestReturnIds:
    @pytest.fixture
    def fake_map(self):
        return {'hello': 1, 'my': 2, 'name': 3, 'is': 4 }
    
    def test_correct_ids(self, fake_map):
        s_response = return_single_ids(fake_map, ('hello', 'name', 'my', 'is'))
        m_response = return_multiple_ids(fake_map, (('hello', 'is'),('my',),('hello', 'my', 'name', 'is')))
        assert s_response == (1,3,2,4)
        assert m_response == ((1,4),(2,),(1,2,3,4))
    
    def test_edge_ids(self, fake_map):
        assert return_multiple_ids(fake_map, (('hello',),)) == ((1,),)
        assert return_single_ids(fake_map,()) == ()
    
    def test_incorrect_id_formats(self, fake_map):
        assert return_single_ids(fake_map, (1,)) == (None,)
        assert return_multiple_ids(fake_map, ((False,),)) == ((None,),)
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

class TestInsertions:
    #TODO: fix or remove this

    # @patch('psycopg2.extras.execute_values')  # Patch execute_values directly
    # def test_adding_judges(self, mock_execute_values, fake_conn):
    #     add_judges(fake_conn, [('a',)])
    #     assert mock_execute_values.call_count == 1
    #     expected_query = """
    #     INSERT INTO judge(judge_name) VALUES %s
    #     ON CONFLICT DO NOTHING;
    #     """
    #     expected_values = [(match_judge('a', get_judges(fake_conn)),)]
    #     mock_execute_values.assert_called_once_with(
    #         fake_conn.cursor.return_value.__enter__.return_value,
    #         expected_query,
    #         expected_values)
    #     fake_conn.commit.assert_called_once()


    def test_adding_judges(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #add_judges(fake_conn, [('a',)])

    def test_adding_tags(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #add_tags(fake_conn, [('a',)])
    
    def test_adding_law_firms(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #add_law_firms(fake_conn, [('a',)])

    def test_adding_participants(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #add_participants(fake_conn, [('a',)])
    
    def test_add_courts(self, fake_conn, fake_cur):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #add_courts(fake_conn, [('a',)])
        
    def test_populating_court_cases(self, fake_conn, fake_cur):
        to_insert = (fake_conn,(('[2003]',),), (('he died',),),((1,),),(('MM v TF',),),(('08/07/05',),),(('2003',),),(('https',),),(('ABC123',),),(('guilty',),))
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #populate_court_case(*to_insert)

    def test_populate_judge_assignment(self, fake_conn, fake_cur):
        to_insert = (fake_conn, '[2003]', (1,))
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #populate_judge_assignment(*to_insert)
    
    def test_populate_tag_assignment(self, fake_conn, fake_cur):
        to_insert = (fake_conn, 1, (1,))
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #populate_tag_assignment(*to_insert)
    
    def test_populate_lawyer_assignment(self, fake_conn, fake_cur):
        to_insert = (fake_conn, ['John Smith'], [1])
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #populate_lawyer(*to_insert)
    
    def test_populate_participant_assignment(self, fake_conn, fake_cur):
        to_insert = (fake_conn, [((1,(1,1)),(2,(2,2),3,(3,3)))])
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ()
        #populate_participant_assignment(*to_insert)
        
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
        print(result)
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

class TestInsertAll:
    
    @pytest.fixture
    def example_data(self): #2 cases
        return {
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
    
    def test_all_data_insertion(self, fake_conn, fake_cur, example_data):
        fake_conn.cursor.return_value.__enter__.return_value = fake_cur
        fake_cur.execute_values.return_values = ('',)
        # result = insert_to_database(fake_conn, example_data)
        # assert result == 'done'

