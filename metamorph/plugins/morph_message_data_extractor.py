#!/usr/bin/python
import argparse
import logging
import json

from metamorph.lib.support_functions import setup_logging
from metamorph.metamorph_plugin import MetamorphPlugin


class MessageDataExtractor(MetamorphPlugin):
    """
    Metadata Extractor from CI messages
    """

    def __init__(self, ci_message_file):
        super().__init__()
        self.ci_message = {}
        self.ci_message_file = ci_message_file

    def get_ci_message_data(self):
        """
        Main function which runs extractor behavior

        :return Json with extracted metadata
        """
        self.read_input_file()
        try:
            if not self.check_valid_ci_message():
                logging.error("Given CI_message does not contain important data.")
                exit(1)
        except KeyError as key_detail:
            logging.error("Given CI_message does not contain important key values. "
                          "Missing key value: {}".format(key_detail))
            exit(1)
        except Exception as detail:
            logging.error("Unexpected error happened during CI message key values extraction. "
                          "See details: {}".format(detail))
            exit(1)
        return self.get_build_data()

    def read_input_file(self):
        """Method for """
        try:
            self.ci_message = self.read_json_file(self.ci_message_file)
        except Exception as detail:
            logging.error("Failed to parse input json file with message: {}".format(detail))
            logging.debug("Failed to parse input json file with message: {0} "
                          "and traceback: {1}".format(detail, detail.__traceback__))
            exit(1)

    def check_valid_ci_message(self):
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
        return message['header']['new'] == 'CLOSED'

    @staticmethod
    def is_component_build(message):
        return message['header']['method'] == "build" and \
            message['header'].get('package') is not None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Get important data from CI message.'
    )
    parser.add_argument(
        'ci_message',
        metavar='<ci-message>',
        help='Input CI message in json format.'
    )
    parser.add_argument(
        '--output',
        metavar='<output-metadata-file>',
        default='metamorph.json',
        help='Output metadata file name where CI Message data will be stored',
        nargs='?')
    return parser.parse_args()


def main():
    setup_logging(default_path="etc/logging.json")
    args = parse_args()
    data_extractor = MessageDataExtractor(args.ci_message)
    ci_message_data = data_extractor.get_ci_message_data()
    data_extractor.write_json_file(ci_message_data, args.output)


if __name__ == '__main__':
    main()
