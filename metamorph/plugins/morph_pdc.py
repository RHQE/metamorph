#!/usr/bin/python
import argparse
import logging
import logging.config

import requests

from metamorph.lib.logging_conf import setup_logging, storing_pretty_json


class PDCApiException(Exception):
    pass


class PDCApi(object):
    pdc_name_mapping = {
        "bugzilla-components": {"name": '{}'},
        "global-components": {"name": '{}'},
        "release-component-contacts": {"component": '^{}$'},
        "release-component-relationships": {"from_component_name": '{}'},
        "release-components": {"name": '{}'},
        "rpms": {"name": '^{}$', "version": '{}', "release": '{}'},
        "global-component-contacts": {"component": '^{}$'}
    }

    pdc_param_mapping = {
        "build-image-rtt-tests": "build_nvr",
    }

    param_mapping = {
        "name": "",
        "version": "",
        "release": ""
    }

    MAX_QUERIED_DATA_SIZE = 20

    def __init__(self, pdc_api_url, ca_cert, component_nvr):
        self.pdc_api_url = pdc_api_url
        self.ca_cert = ca_cert
        self.component_nvr = component_nvr
        self.pdc_proxy = None

    def get_pdc_metadata_by_component_name(self, limit=10):
        component_name, version, release = self.get_component_nvr(self.component_nvr)
        self.setup_pdc_metadata_params(component_name, version, release)
        logging.debug("PDC options by component name are {0} ".format(self.pdc_name_mapping))
        logging.debug("Connecting to PDC api.")
        pdc_metadata = {}
        for pdc_metadata_type in self.pdc_name_mapping:
            url = "{0}/{1}/?".format(self.pdc_api_url, pdc_metadata_type)
            metadata = []
            while url and len(metadata) / self.MAX_QUERIED_DATA_SIZE < limit:
                queried_data = self.query_pdc(url, self.pdc_name_mapping[pdc_metadata_type])
                url = queried_data['next']
                metadata += queried_data['results']
            pdc_metadata[pdc_metadata_type] = metadata
        return pdc_metadata

    def query_pdc(self, url, url_options=dict,):
        """
        This method queries pdc_api with given url and url_option variable

        :param url -- pdc api url
        :param url_options -- dictionary of wanted options

        :returns -- Queried data
        """
        try:
            response = requests.get(url, params=url_options, verify=self.ca_cert)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as detail:
            logging.error("Unsuccessful connection to pdc api url "
                          "with url=\"{0}\" and options=\"{1}\"".format(url, url_options))
            raise PDCApiException("Unsuccessful connection to pdc api url with detail= \"{}\"".format(detail))

    def setup_pdc_metadata_params(self, name, version, release):
        for pdc_metadata_type in self.pdc_name_mapping:
            for param in self.pdc_name_mapping[pdc_metadata_type]:
                param_value = self.pdc_name_mapping[pdc_metadata_type][param]
                self.pdc_name_mapping[pdc_metadata_type][param] = param_value.format(self.get_param_value(param,
                                                                                                          name,
                                                                                                          version,
                                                                                                          release))

    def get_param_value(self, param, name, version, release):
        if self.is_name_param(param):
            return name
        elif self.is_version_param(param):
            return version
        elif self.is_release_param(param):
            return release
        error_message = "Unknown pdc parameter {}".format(param)
        raise PDCApiException(error_message)

    @staticmethod
    def is_release_param(param_value):
        return param_value == "release"

    @staticmethod
    def is_version_param(param_value):
        return param_value == "version"

    @staticmethod
    def is_name_param(param_value):
        name_mappings = ['name', 'from_component_name', 'component']
        return param_value in name_mappings

    @staticmethod
    def get_component_nvr(component_nvr):
        splitted_name = component_nvr.split("-")
        return splitted_name[0], splitted_name[1], splitted_name[2]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Get metadata from PDC.'
    )
    parser.add_argument(
        '--component-nvr',
        metavar='<nvr>',
        required=True,
        help='Component in nvr format.'
    )
    parser.add_argument(
        '--pdc-api-url',
        metavar='<api-url>',
        required=True,
        help='PDC api url.'
    )
    parser.add_argument(
        '--ca-cert',
        default='/etc/ssl/certs/ca-bundle.crt',
        help='Path to CA certificate file or directory'
    )
    parser.add_argument(
        '--output',
        metavar='<output-metadata-file>',
        default='metamorph.json',
        help='Output metadata file name where PDC metadata will be stored',
    )
    return parser.parse_args()


def main():
    setup_logging(default_path="metamorph/etc/logging.json")
    args = parse_args()
    client = PDCApi(args.pdc_api_url, args.ca_cert, args.component_nvr)
    pdc_metadata = client.get_pdc_metadata_by_component_name()
    storing_pretty_json(dict(results=pdc_metadata), args.output)

if __name__ == '__main__':
    main()
