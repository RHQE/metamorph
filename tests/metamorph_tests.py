import unittest
from metamorph.plugins.morph_pdc import PDCApi


class MyTestCase(unittest.TestCase):
    def test_dummy(self):
        self.assertEqual(True, True)

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
