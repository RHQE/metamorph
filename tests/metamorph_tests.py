import unittest
import json
import os

from metamorph.plugins.morph_message_data_extractor import MessageDataExtractor
from metamorph.library.message_data_extractor import MessageDataExtractor as MessageDataExtractorAnsible
from metamorph.plugins.morph_messagehub import env_run
from metamorph.plugins.morph_resultsdb import ResultsDBApi
from metamorph.plugins.morph_pdc import PDCApi
from metamorph.library.pdc import PDCApi as PDCApiAnsible


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
    # End of message data extractor tests

    # Messagehub testing section 
    def test_env_message_part(self):
        data = {"old": "OPEN", "new": "FAILED", "attribute": "state"}
        os.environ['TEST'] = json.dumps(data)
        output = env_run(SimpleClass('TEST'))
        self.assertDictEqual(output, data)

    @unittest.skip("Travis CI does not have access to RH site.")
    def test_resultdb_query(self):
        resultsdb = ResultsDBApi("", "kernel-3.10.0-632.el7", "1", "https://url.corp.redhat.com/resultdb2", "")
        self.assertEqual(len(resultsdb.get_resultsdb_data()), 200)
    # End of message data extractor tests

    # Messagehub testing section
    def test_env_message_part_with_newlines(self):
        data = '{\n"old": \n"OPEN", \n"new": \n"FAILED", \n"attribute": \n"state"}'
        data_without_newlines = {"old": "OPEN", "new": "FAILED", "attribute": "state"}
        os.environ['TEST'] = data
        output = env_run(SimpleClass('TEST'))
        self.assertDictEqual(output, data_without_newlines)
    # End of Messagehub testing section

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

    # resultsDB tests
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
    # End of resultsDB tests

    # PDC tests
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

    def test_pdc_rpm_mappings(self):
        client = PDCApi("", "", "bash-completion-version-release")
        with open("./tests/sources/test_rpm_mappings.json") as rpm_mapping_input:
            pdc_data = json.load(rpm_mapping_input)
        output = {'rhel-7.1', 'rhel-7.0'}
        self.assertSetEqual(client.get_release_ids(pdc_data['release-components'], pdc_data['rpms']), output)

    def test_release_id_to_compose_getter(self):
        compose = "COMPONENT-9-xxx"
        client = PDCApi("", "", "component-version-release")
        release = client.get_release_id_from_compose(compose)
        self.assertEqual(release, 'component-9')

    def test_get_release_ids(self):
        release_components = [{"release": {"release_id": "component-9.0"}},
                              {"release": {"release_id": "component-9.1"}}]
        rpms = [{"linked_composes": ["COMPONENT-9.0-xxx", "COMPONENT-9.0-xxx"]},
                {"linked_composes": ["COMPONENT-9.1-xxx", "COMPONENT-9.1-xxx"]}]
        client = PDCApi("", "", "component-version-release")
        self.assertSetEqual(client.get_release_ids(release_components, rpms), {'component-9.0', 'component-9.1'})

    def test_component_nvr(self):
        client = PDCApi("", "", "component-version-release")
        component = "name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('name', 'version', 'release'))
        component = "sec-name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('sec-name', 'version', 'release'))
        component = "first-sec-third-name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('first-sec-third-name', 'version', 'release'))

    def test_pdc_param_setup_ansible(self):
        client = PDCApiAnsible("", "", "component-version-release")
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

    def test_pdc_rpm_mappings_ansible(self):
        client = PDCApiAnsible("", "", "bash-completion-version-release")
        with open("./tests/sources/test_rpm_mappings.json") as rpm_mapping_input:
            pdc_data = json.load(rpm_mapping_input)
        output = {'rhel-7.1', 'rhel-7.0'}
        self.assertSetEqual(client.get_release_ids(pdc_data['release-components'], pdc_data['rpms']), output)

    def test_release_id_to_compose_getter_ansible(self):
        compose = "COMPONENT-9-xxx"
        client = PDCApiAnsible("", "", "component-version-release")
        release = client.get_release_id_from_compose(compose)
        self.assertEqual(release, 'component-9')

    def test_get_release_ids_ansible(self):
        release_components = [{"release": {"release_id": "component-9.0"}},
                              {"release": {"release_id": "component-9.1"}}]
        rpms = [{"linked_composes": ["COMPONENT-9.0-xxx", "COMPONENT-9.0-xxx"]},
                {"linked_composes": ["COMPONENT-9.1-xxx", "COMPONENT-9.1-xxx"]}]
        client = PDCApiAnsible("", "", "component-version-release")
        self.assertSetEqual(client.get_release_ids(release_components, rpms), {'component-9.0', 'component-9.1'})

    def test_component_nvr_ansible(self):
        client = PDCApiAnsible("", "", "component-version-release")
        component = "name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('name', 'version', 'release'))
        component = "sec-name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('sec-name', 'version', 'release'))
        component = "first-sec-third-name-version-release"
        self.assertTupleEqual(client.get_component_nvr(component), ('first-sec-third-name', 'version', 'release'))
    # End of PDC tests

if __name__ == '__main__':
    unittest.main()
