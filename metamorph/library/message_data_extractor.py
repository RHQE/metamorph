#!/usr/bin/python
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
---
module: message_data_extractor
short_description: Get important metadata from CI-message.
version_added: 2.3.0
author: Jiri Kulda (@Jurisak)
options:
  ci-message:
    description:
      - Input CI message in json format.
    required: true

  output:
    description:
      - Output metadata file name where CI Message metadata will be stored.
    required: false
    default: metamorph.json
'''

EXAMPLES = '''
- name: Get metadata from CI-message
  message_data_extractor:
    ci-message: path_to/ci-message.json
  register: result
'''

RETURN = '''
Error message:
  description: An error occurred during metadata extraction
  returned: Error
  type: dictionary
  sample:  { "changed": false, "failed": true, "module_stderr": Given CI_message does not contain
                                                                important key values. Missing key
                                                                value: 'header'"
CI-message metadata:
  description: Extracted CI-message metadata
  returned: changed
  type: dictionary
  sample: { "changed": true, "meta": { "messages": { "owner": "jkulda",
                                                     "package": "setup",
                                                     "release": "5.el7_1",
                                                     "scratch": "true",
                                                     "target": "rhel-*-*",
                                                     "version": "2.8.71"}}
'''

import logging
import traceback

from metamorph.lib.support_functions import setup_logging
from metamorph.metamorph_plugin import MetamorphPlugin
from ansible.module_utils.basic import AnsibleModule


class CIMessageKeyValueException(Exception):
    """CI Message key value exception class"""
    pass


class CIMessageReadingException(Exception):
    """CI Message reading exception class"""
    pass


class MessageDataExtractor(MetamorphPlugin):
    """
    Metadata Extractor from CI messages
    """

    def __init__(self, ci_message_file):
        super().__init__()
        self.ci_message = {}
        self.ci_message_file = ci_message_file
        self.error_message = ""

    def get_ci_message_data(self):
        """
        Main function which runs extractor behavior

        :return Json with extracted metadata
        """
        self.read_input_file()
        try:
            if not self.check_valid_ci_message():
                raise CIMessageKeyValueException("Given CI_message does not contain "
                                                 "important data.")
        except KeyError as key_detail:
            raise CIMessageKeyValueException("Given CI_message does not contain important key "
                                             "values. Missing key value: {}".format(key_detail))
        return self.get_build_data()

    def read_input_file(self):
        """Method for reading input ci message file"""
        try:
            self.ci_message = self.read_json_file(self.ci_message_file)
        except FileNotFoundError as detail:
            logging.debug("Failed to parse input json file because file was not found: {0} "
                          "and traceback: {1}".format(detail, traceback.print_exc()))
            raise CIMessageReadingException("Failed to parse input json file with because file "
                                            "was not found with message: {}".format(detail))
        except ValueError as detail:
            logging.debug("Failed to parse input json file with message: {0} "
                          "and traceback: {1}".format(detail, traceback.print_exc()))
            raise CIMessageReadingException("Failed to parse input json file "
                                            "with message: {}".format(detail))

    def check_valid_ci_message(self):
        """
        Method for checking whether method contain needed data

        :return Boolean
        """
        return self.is_closed_build(self.ci_message) and self.is_component_build(self.ci_message)

    def get_build_data(self):
        """
        Method for getting concrete data from ci_message

        :returns json with extracted metadata
        """
        return dict(
            package=self.ci_message['header']['package'],
            release=self.ci_message['header']['release'],
            version=self.ci_message['header']['version'],
            target=self.ci_message['header']['target'],
            owner=self.ci_message['header']['owner'],
            scratch=self.ci_message['header'].get('scratch', 'false')
        )

    @staticmethod
    def is_closed_build(message):
        """
        Method for checking whether ci message is type of closed build

        :param message -- CI message which will be checked

        :return Boolean
        """
        return message['header']['new'] == 'CLOSED'

    @staticmethod
    def is_component_build(message):
        """
        Method for checking whether given CI message is from component build

        :param message -- CI message which will be checked

        :return Boolean
        """
        return message['header']['method'] == "build" and \
            message['header'].get('package') is not None


def main():
    """Main function which manages plugin behavior"""
    extractor_args = {
        "ci-message": {"type": "str", "required": True},
        "output": {"type": "str", "default": "metamorph.json"}
    }
    setup_logging(default_path="etc/logging.json")
    module = AnsibleModule(argument_spec=extractor_args)
    data_extractor = MessageDataExtractor(module.params['ci-message'])
    ci_message_data = {}
    try:
        ci_message_data = data_extractor.get_ci_message_data()
    except CIMessageKeyValueException or CIMessageReadingException as detail:
        module.fail_json(msg=detail)
    except Exception as detail:
        module.fail_json(msg=detail)

    data_extractor.write_json_file(dict(ci_message_data=ci_message_data), module.params['output'])
    module.exit_json(changed=True, meta=dict(ci_message_data=ci_message_data))


if __name__ == '__main__':
    main()
