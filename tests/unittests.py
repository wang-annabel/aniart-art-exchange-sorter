import unittest
import app.matching as matching
import pandas as pd
from pandas.testing import assert_frame_equal
from app.graph import cycles


class InputTests(unittest.TestCase):
    def test_form_response_to_input(self):
        res_df = matching.form_response_to_input("test_input/raw_form_data.csv")
        assert_frame_equal(res_df, pd.read_csv("test_input/input_short.csv"))

    def test_noncsv_form_response_to_input(self):
        with self.assertRaises(TypeError):
            matching.form_response_to_input('../main.py')

    def test_invalid_format_form_response_to_input(self):
        with self.assertRaises(KeyError):
            matching.form_response_to_input('test_input/raw_form_data_1participant.csv')

class GraphTests(unittest.TestCase):
    def test_get_number_of_cycles_in_single_cycle_graph(self):
        nodes = [1,2,3,4,5,6,7,8,9,10]
        links = [{'source':1,'target':2},
                 {'source':2,'target':3},
                 {'source':3,'target':4},
                 {'source':4,'target':5},
                 {'source':5,'target':6},
                 {'source':6,'target':7},
                 {'source':7,'target':8},
                 {'source':8,'target':9},
                 {'source':9,'target':10},
                 {'source':10,'target':1}]
        self.assertEqual(cycles(nodes,links),1)

    def test_get_number_of_cycles_with_orphans(self):
        nodes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        links = [{'source': 1, 'target': 2},
                 {'source': 2, 'target': 3},
                 {'source': 3, 'target': 4},
                 {'source': 4, 'target': 5},
                 {'source': 5, 'target': 6},
                 {'source': 6, 'target': 7},
                 {'source': 7, 'target': 8},
                 {'source': 8, 'target': 9},
                 {'source': 9, 'target': 1},] # 10 is orphaned
        self.assertEqual(cycles(nodes, links),1)

    def test_get_number_of_cycles_with_multiple_cycles(self):
        nodes = [1, 2, 3, 4, 5, 6, 7, 8]
        links = [{'source': 1, 'target': 2},
                 {'source': 2, 'target': 3},
                 {'source': 3, 'target': 4},
                 {'source': 4, 'target': 1},
                 {'source': 5, 'target': 6},
                 {'source': 6, 'target': 7},
                 {'source': 7, 'target': 8},
                 {'source': 8, 'target': 5},]
        self.assertEqual(cycles(nodes,links),2)

if __name__ == '__main__':
    unittest.main()
