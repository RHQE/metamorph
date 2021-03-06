import logging
import logging.config
import json
import time
import os
import yaml

import requests


class MetamorphPlugin(object):

    def __init__(self):
        pass

    @staticmethod
    def write_json_file(input_data, output="metamorph.json"):
        if os.path.isfile(output):
            with open(output) as existing_metamorph:
                existing_metadata = json.load(existing_metamorph)
            plugin_name = list(input_data)[0]
            if 'metamorph' in existing_metadata.keys():
                existing_metadata['metamorph'][plugin_name] = input_data[plugin_name]
                with open(output, 'w') as metamorph:
                    json.dump(existing_metadata, metamorph, indent=2)
            else:
                raise LookupError("ERROR: Wrong format of given '{}'. "
                                  "'metamorph' must be root element".format(output))
        else:
            with open(output, "w") as metamorph:
                json.dump(dict(metamorph=input_data), metamorph, indent=2)

    @staticmethod
    def read_json_file(input_file):
        with open(input_file, "r") as message:
            return json.load(message)

    @staticmethod
    def write_yaml_file(output_data, destination):
        try:
            with open(destination, 'w') as destination_fp:
                yaml.dump(output_data, destination_fp)
        except IOError:
            raise LookupError('Destination path "{}" was not found. '
                              'Please check destination output path'.format(destination))

    @staticmethod
    def read_yaml_file(input_file):
        with open(input_file, "r") as message:
            return yaml.load(message)

    def query_api(self, url, url_options=dict, attempt=0, ca_cert='/etc/ssl/certs/ca-bundle.crt'):
        """
        This method queries given url with url_option variable

        :param url -- api url
        :param url_options -- dictionary of wanted options
        :param attempt -- number of query tries if some problem occurs. Maximum is 3.
        :param ca_cert -- path to certificates to verify url

        :returns -- Queried data
        """
        try:
            response = requests.get(url, params=url_options, verify=ca_cert)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as detail:
            if attempt < 3:
                logging.info("An exception occurred while querying url: '{}'. "
                             "Trying again after one minute.".format(url))
                attempt += 1
                time.sleep(60)  # Sleeping for one minute
                self.query_api(url, url_options, attempt, ca_cert)
            else:
                logging.error("ERROR: Unable to access url '{0}' with given options '{1}'.".format(url, url_options))
                logging.error("ERROR: {0}".format(detail.args))
