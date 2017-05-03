import unittest
import json
import os

from metamorph.plugins.morph_message_data_extractor import MessageDataExtractor
from metamorph.library.message_data_extractor import MessageDataExtractor as MessageDataExtractorAnsible
from metamorph.plugins.morph_messagehub import env_run
from metamorph.plugins.morph_resultsdb import ResultsDBApi


class SimpleClass(object):
    def __init__(self, env_variable):
        self.env_variable = env_variable


class MyTestCase(unittest.TestCase):

    def test_data_extractor_pass(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "build",
                              "target": "rhel-7.1-candidate",
                              "new": "CLOSED",
                              "package": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        output = {'scratch': 'true',
                  'version': '2.8.71',
                  'owner': 'jkulda',
                  'release': '5.el7_1',
                  'package': 'setup',
                  'target': 'rhel-7.1-candidate'}
        extractor = MessageDataExtractor(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), True)
        self.assertEqual(extractor.get_build_data(), output)

    def test_data_extractor_check_fail(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "buildArch",
                              "target": "rhel-7.1-candidate",
                              "new": "CLOSED",
                              "packages": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        extractor = MessageDataExtractor(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), False)

    def test_data_extractor_check_fail2(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "build",
                              "target": "rhel-7.1-candidate",
                              "new": "RUNNING",
                              "packages": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        extractor = MessageDataExtractor(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), False)

    def test_data_extractor_pass_ansible(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "build",
                              "target": "rhel-7.1-candidate",
                              "new": "CLOSED",
                              "package": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        output = {'scratch': 'true',
                  'version': '2.8.71',
                  'owner': 'jkulda',
                  'release': '5.el7_1',
                  'package': 'setup',
                  'target': 'rhel-7.1-candidate'}
        extractor = MessageDataExtractorAnsible(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), True)
        self.assertEqual(extractor.get_build_data(), output)

    def test_data_extractor_check_fail_ansible(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "buildArch",
                              "target": "rhel-7.1-candidate",
                              "new": "CLOSED",
                              "packages": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        extractor = MessageDataExtractorAnsible(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), False)

    def test_data_extractor_check_fail2_ansible(self):
        message = {'message': {"weight": 0.2, "parent": None},
                   'header': {"owner": "jkulda",
                              "scratch": "true",
                              "method": "build",
                              "target": "rhel-7.1-candidate",
                              "new": "RUNNING",
                              "packages": "setup",
                              "version": "2.8.71",
                              "release": "5.el7_1"
                              }
                   }
        extractor = MessageDataExtractorAnsible(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), False)

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

    # Messagehub testing section
    def test_env_message_part(self):
        data = {"old": "OPEN", "new": "FAILED", "attribute": "state"}
        os.environ['TEST'] = json.dumps(data)
        output = env_run(SimpleClass('TEST'))
        self.assertDictEqual(output, data)

    def test_env_message_part_with_newlines(self):
        data = '{\n"old": \n"OPEN", \n"new": \n"FAILED", \n"attribute": \n"state"}'
        data_without_newlines = {"old": "OPEN", "new": "FAILED", "attribute": "state"}
        os.environ['TEST'] = data
        output = env_run(SimpleClass('TEST'))
        self.assertDictEqual(output, data_without_newlines)
    # End of messagehub testing section

if __name__ == '__main__':
    unittest.main()
