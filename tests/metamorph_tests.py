import unittest
import json
from metamorph.plugins.morph_resultsdb import ResultsDBApi
from metamorph.plugins.morph_pdc import PDCApi


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)

    def test_resultdb_output(self):
        resultsdb = ResultsDBApi("", "", "", "", "")
        with open("./tests/sources/resultsdb_output.json") as resultsdb_output:
            data = {'setup-2.8.71-5.el7_1': json.load(resultsdb_output)['data']}
        resultsdb.job_names_result = data
        method_result = resultsdb.format_result()
        with open("./tests/sources/resultsdb_output_result.json") as resultsdb_output_result:
            self.assertDictEqual(method_result, json.load(resultsdb_output_result))

    def test_resultdb_output1(self):
        resultsdb = ResultsDBApi("", "", "", "", "")
        with open("./tests/sources/resultsdb_output1.json") as resultsdb_output:
            data = {'setup-2.8.71-5.el7_1': json.load(resultsdb_output)['data']}
        resultsdb.job_names_result = data
        self.assertRaises(KeyError, resultsdb.setup_output_data, [data])

    @unittest.skip("Travis CI does not have access to RH site.")
    def test_resultdb_query(self):
        resultsdb = ResultsDBApi("", "kernel-3.10.0-632.el7", "1", "https://url.corp.redhat.com/resultdb2", "")
        self.assertEqual(len(resultsdb.get_resultsdb_data()), 200)

    def test_pdc_param_setup(self):
        client = PDCApi("", "", "component-version-release")
        output = {
            "bugzilla-components": {"name": 'component'},
            "global-components": {"name": 'component'},
            "release-component-contacts": {"component": '^component$'},
            "release-component-relationships": {"from_component_name": 'component'},
            "release-components": {"name": 'component'},
            "rpms": {"name": '^component$', "version": 'version', "release": 'release'},
            "global-component-contacts": {"component": '^component$'}
        }
        client.setup_pdc_metadata_params("component", "version", "release")
        self.assertDictEqual(client.pdc_name_mapping, output)


if __name__ == '__main__':
    unittest.main()
