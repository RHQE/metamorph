#!/usr/bin/python
import argparse
import logging
import logging.config

import requests

from metamorph.lib.logging_conf import setup_logging, storing_pretty_json


class PDCApiException(Exception):
    pass


class PDCApi(object):
    """
    PDCApi class for extracting metadata from pdc
    """
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
        """
        Method for extracting metadata from pdc
        :param limit -- Limit for amount of queried pages from pdc

        :returns -- Dictionary of extracted metadata from pdc
        """
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
        pdc_metadata['rpm-mapping'] = self.get_rpm_mappings(component_name, pdc_metadata['release-components'],
                                                            pdc_metadata['rpms'])
        return pdc_metadata

    def get_rpm_mappings(self, component_name, release_components, rpms):
        """
        Method for getting rpm-mappings metadata from pdc
        :param component_name -- Name of given component
        :param release_components -- Extracted release-components from pdc
        :param rpms -- Extracted release-components from pdc

        :returns Dictionary of rpm-mapping for given component-name
        """
        release_ids = self.get_release_ids(release_components, rpms)
        rpm_mappings = dict()
        for release_id in release_ids:
            rpm_mapping_url = "{0}/releases/{1}/rpm-mapping/{2}/?".format(self.pdc_api_url, release_id, component_name)
            rpm_mappings[release_id] = self.query_pdc(rpm_mapping_url)
        return rpm_mappings

    def get_release_ids(self, release_components, rpms):
        """
        Method for release_ids extraction
        This method extracts all component releases from release-components data
        After that are tested with with compose names
        release_id is accepted when compose name and release_id form release-components are matching

        :param release_components -- Extracted release-components from pdc
        :param rpms -- Extracted rpms from pdc

        :returns Set of release_ids
        """
        release_components_release_ids = set()
        release_ids = set()
        for release_component in release_components:
            release_components_release_ids.add(release_component['release']['release_id'])

        for component_rpm in rpms:
            for linked_compose in component_rpm['linked_composes']:
                compose_release_id = self.get_release_id_from_compose(linked_compose)
                if compose_release_id in release_components_release_ids:
                    release_ids.add(compose_release_id)
        return release_ids

    @staticmethod
    def get_release_id_from_compose(compose):
        """
        Method for parsing release_id from compose name

        :param compose -- Compose name

        :returns String which contains release_id parsed from compose name
        """
        splitted_compose = compose.split('-')
        return splitted_compose[0].lower() + '-' + splitted_compose[1]

    def query_pdc(self, url, url_options=None):
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
            logging.error('Unsuccessful connection to pdc api url '
                          'with url="{0}" and options="{1}"'.format(url, url_options))
            raise PDCApiException('Unsuccessful connection to pdc api url with detail= "{}"'.format(detail))

    def setup_pdc_metadata_params(self, name, version, release):
        """
        Method for pdc metadata parameters setup with given data
        :param name -- Component name
        :param version -- Component version
        :param release -- Component release
        """
        for pdc_metadata_type in self.pdc_name_mapping:
            for param, param_value in self.pdc_name_mapping[pdc_metadata_type].items():
                self.pdc_name_mapping[pdc_metadata_type][param] = param_value.format(self.get_param_value(param,
                                                                                                          name,
                                                                                                          version,
                                                                                                          release))

    def get_param_value(self, param, name, version, release):
        """
        Method for returning correct parameter value by its name
        :param param -- Name of parameter for pdc metadata type
        :param name -- Component name
        :param version -- Component version
        :param release -- Component release

        :returns String which contains value for given parameter (param)
        """
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
        """
        Method for checking whether given parameter is release
        :param param_value -- Parameter name

        :returns Boolean value
        """
        return param_value == "release"

    @staticmethod
    def is_version_param(param_value):
        """
        Method for checking whether given parameter is version
        :param param_value -- Parameter name

        :returns Boolean value
        """
        return param_value == "version"

    @staticmethod
    def is_name_param(param_value):
        """
        Method for checking whether given parameter is name
        :param param_value -- Parameter name

        :returns Boolean value
        """
        name_mappings = ['name', 'from_component_name', 'component']
        return param_value in name_mappings

    @staticmethod
    def get_component_nvr(component_nvr):
        """
        Method for extracting nvr from given nvr string
        :param component_nvr -- component in nvr format

        :returns tuple which contain component_name, version and release
        """
        splitted_name = component_nvr.split("-")
        component_name = ''
        for name in splitted_name[:-2]:
            component_name += name + '-'
        return component_name[:-1], splitted_name[-2], splitted_name[-1]


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
    storing_pretty_json(dict(pdc=dict(results=pdc_metadata)), args.output)

if __name__ == '__main__':
    main()
