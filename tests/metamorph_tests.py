import unittest
import json
from metamorph.plugins.morph_resultsdb import ResultsDBApi
from metamorph.plugins.morph_provision import Provision, ProvisionException


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)

    # ResultsDB testing
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
    # End of ResultsDB testing

    # Provision testing
    def test_metadata_path_getter(self):
        provision = Provision('', '', '', '')
        path = provision.get_git_repo_name('https://github.com/Jurisak/metamorph.git')
        self.assertEqual(path, 'metamorph')

    def test_topology_setup(self):
        provision = Provision('', '', '', '')
        provision.setup_topology_by_osp_config('./tests/sources/osp_config.json')
        res_defs = {
            "res_name": "unknown_inst",
            "flavor": u"m1.large",
            "res_type": "os_server",
            "keypair": u"team-jenkins",
            "count": u'1',
            "image": u"fedora-20_image",
            "networks": [
                u"team-jenkins"
            ]
        }
        self.assertDictEqual(provision.res_defs, res_defs)

    def test_clone_repo(self):
        provision = Provision('', '', '', '')
        provision.clone_git_repository('https://github.com/Jurisak/bkrdoc.git')

    def test_minimal_topology(self):
        provision = Provision('', '', '', '')
        provision.setup_topology_by_osp_config('./tests/sources/osp_config1.json')
        res_defs = {
            "res_name": "unknown_inst",
            "flavor": "m1.small",
            "res_type": "os_server",
            "keypair": u"team-jenkins",
            "count": '1',
            "image": u"fedora-20_image",
            "networks": [
                u"team-jenkins"
            ]
        }
        self.assertDictEqual(provision.res_defs, res_defs)

    def test_get_metadata_by_location(self):
        metadata = {'path': {'to': {'metadata': 'goal'}}}
        metadata_location = {'metadata': ['path', 'to', 'metadata']}
        provision = Provision('', '', '', '')
        self.assertEqual('goal', provision.get_metadata_from_location(metadata, metadata_location['metadata'],
                                                                      'metadata'))

    def test_get_metadata_by_location2(self):
        metadata = {'path': {'to': {'metadata': 'goal'}}}
        metadata_location = {'metadata': ['path', 'to']}
        provision = Provision('', '', '', '')
        self.assertEqual('goal', provision.get_metadata_from_location(metadata, metadata_location['metadata'],
                                                                      'metadata'))

    def test_get_metadata_by_location_failed(self):
        metadata = {'path': {'to': {'metadata': 'goal'}}}
        metadata_location = {'metadata': ['path', 'metadata']}
        provision = Provision('', '', '', '')
        self.assertRaises(KeyError, provision.get_metadata_from_location, metadata, metadata_location['metadata'],
                          'metadata')

    def test_topology_credential_creation(self):
        provision = Provision('', '', '', '')
        provision.setup_topology_by_osp_config('./tests/sources/osp_config1.json')
        credentials = provision.get_openstack_credentials(provision.osp_data)
        credentials_output = {'_openstack.yaml': {'endpoint': '', 'password': '', 'project': '', 'username': ''}}

        self.assertDictEqual(credentials_output, credentials)

    def test_metadata_extraction(self):
        provision = Provision('', '', '', '')
        metadata_location = {'count': ['project', 'info', 'something', 'source_count'],
                             'keypair': ['project', 'info', 'something', 'keypair']}
        provision.setup_topology_by_metadata('./tests/sources/metadata.yaml', metadata_location)
        res_defs = {
            'res_name': "unknown_inst",
            'flavor': "m1.small",
            'res_type': "os_server",
            'image': "",
            'count': '3',
            'keypair': "some_keypair",
            'networks': []
        }
        self.assertDictEqual(provision.res_defs, res_defs)

    def test_metadata_extraction_failure(self):
        provision = Provision('', '', '', '')
        metadata_location = {'count': ['project', 'info', 'something'],
                             'keypair': ['project', 'info', 'something']}
        self.assertRaises(ProvisionException, provision.setup_topology_by_metadata, './tests/sources/metadata.yaml',
                          metadata_location)
    # End of Provision testing


if __name__ == '__main__':
    unittest.main()
