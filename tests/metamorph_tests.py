import unittest
from plugins.message_data_extractor import MessageDataExtractor


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
        output = {'scratch': 'true',
                  'version': '2.8.71',
                  'owner': 'jkulda',
                  'release': '5.el7_1',
                  'package': 'setup',
                  'target': 'rhel-7.1-candidate'}
        extractor = MessageDataExtractor(None)
        extractor.ci_message = message
        self.assertEqual(extractor.check_valid_ci_message(), False)

if __name__ == '__main__':
    unittest.main()
