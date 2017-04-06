import unittest
import json
from plugins.morph_resultsdb import ResultsDBApi


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)

    def test_resultdb_output(self):
        resultsdb = ResultsDBApi("", "", "", "")
        with open("./tests/sources/resultsdb_output.json") as resultsdb_output:
            data = {'setup-2.8.71-5.el7_1': json.load(resultsdb_output)['data']}
        resultsdb.job_names_result = data
        method_result = resultsdb.format_result()
        with open("./tests/sources/resultsdb_output_result.json") as resultsdb_output_result:
            self.assertDictEqual(method_result, json.load(resultsdb_output_result))

    def test_resultdb_output1(self):
        resultsdb = ResultsDBApi("", "", "", "")
        with open("./tests/sources/resultsdb_output1.json") as resultsdb_output:
            data = {'setup-2.8.71-5.el7_1': json.load(resultsdb_output)['data']}
        resultsdb.job_names_result = data
        self.assertRaises(KeyError, resultsdb.setup_output_data, [data])

    def test_resultdb_query(self):
        resultsdb = ResultsDBApi("", "kernel-3.10.0-632.el7", "1", "https://url.corp.redhat.com/resultdb2")
        self.assertEqual(len(resultsdb.get_jobs_by_nvr_and_tier()), 200)


if __name__ == '__main__':
    unittest.main()
