#!/usr/bin/python
import argparse
import logging
import logging.config
import json
import time
import os

import requests

from metamorph.lib.support_functions import setup_logging, write_json_file


class ResultsDBApiException(Exception):
    pass


class ResultsDBApi(object):
    """
    Class to communicate and process data with resultsDB
    """
    TIMEOUT_LIMIT = 7200  # Wait 2 hours maximally
    RESULTSDB_LIMITER = 10
    MINUTE = 60  # 60 seconds

    def __init__(self, job_names, component_nvr, test_tier, resultsdb_api_url, ca_bundle):
        self.resultsdb_api_url = resultsdb_api_url
        self.job_names = job_names
        self.job_names_result = {}
        self.ca_bundle_path = ca_bundle
        self.tier_tag = True
        self.url_options = {'CI_tier': test_tier, 'item': component_nvr}

    def get_test_tier_status_metadata(self):
        """
        Method get_resultsdb_data it's the main function from which data are received

        :returns -- dictionary where keys are job names and their values are list of queried data
        """
        if self.job_names:
            for job_name in self.job_names:
                self.job_names_result[job_name] = self.get_resultsdb_data(job_name)
            self.erase_duplicity_results()
            return self.job_names_result
        else:
            queried_data = self.get_resultsdb_data(limit=self.RESULTSDB_LIMITER)
            self.job_names_result = self.setup_output_data(queried_data)
            self.erase_duplicity_results()
            return self.job_names_result

    def erase_duplicity_results(self):
        for job_name in self.job_names_result:
            job_name_data = []
            ref_urls = set()
            for single_result in self.job_names_result[job_name]:
                if single_result['ref_url'] not in ref_urls:
                    job_name_data.append(single_result)
                    ref_urls.add(single_result['ref_url'])
            self.job_names_result[job_name] = job_name_data

    def query_resultsdb(self, url, url_options=dict, attempt=0):
        """
        This method queries resultsDB with given url and url_option variable

        :param url -- resultdb api url
        :param url_options -- dictionary of wanted options
        :param attempt -- number of query tries if some problem occurs

        :returns -- Queried data
        """
        try:
            response = requests.get(url, params=url_options, verify=self.ca_bundle_path)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as detail:
            if attempt < 3:
                logging.info("An exception occurred while querying resultsdb site. Trying again after one minute.")
                attempt += 1
                time.sleep(self.MINUTE)
                self.query_resultsdb(url, url_options, attempt)
            else:
                logging.error("ERROR: Unable to access resultsdb site.")
                logging.error("ERROR: {0}".format(detail.args))

    def get_resultsdb_data(self, job_name="", limit=10):
        """
        Method for getting data from resultsDB

        :param self.url_options -- class dictionary of url options
        :param job_name -- job name which will be searched in resultsDB
        :param limit -- Limit for amount of queried pages from resultsDB
        :returns -- List of queried data
        """
        i = 0
        next_page = ""
        queried_data = []
        if job_name:
            self.url_options['job_name'] = job_name
        while next_page is not None and self.TIMEOUT_LIMIT and limit > i:
            self.url_options['page'] = i
            response_data = self.query_resultsdb(self.resultsdb_api_url, self.url_options)
            if not response_data['data']:
                logging.info("job name has not published results to resultsDB yet, sleeping...")
                time.sleep(self.MINUTE)  # Sleeping for 1 minute
                self.TIMEOUT_LIMIT -= self.MINUTE
            else:
                i += 1
                next_page = response_data['next']
                queried_data += response_data['data']
        if self.TIMEOUT_LIMIT == 0:
            raise ResultsDBApiException("Timeout limit reached and no data were queried.")
        return queried_data

    @staticmethod
    def setup_output_data(resultsdb_data):
        """
        Method for setting up data from get_job_by_nvr_and_tier method.
        Data needs to be in dictionary where keys will be job names

        :param resultsdb_data -- data which were queried without job_name option
        :returns -- dictionary where keys are job names and their values are list of queried data
        """
        formatted_output = {}
        for single_job in resultsdb_data:
            job_names_key = single_job['data'].get('job_name', ['UNKNOWN'])[0]
            if job_names_key in formatted_output.keys():
                formatted_output[job_names_key].append(single_job)
            else:
                formatted_output[job_names_key] = [single_job]
        return formatted_output

    def format_result(self):
        """
        Method which format's queried dictionary from upper methods
        Need's to have it in predefined output format.
        See: tests/sources/resultdsdb_output_result.json

        :returns -- Formatted dictionary
        """
        ci_tier = dict(ci_tier=self.url_options['CI_tier'],
                       nvr=self.url_options['item'],
                       job_name=[],
                       tier_tag=False)
        for single_job in self.job_names_result:
            ci_tier['job_name'].append({single_job: self.format_job_name_result(self.job_names_result[single_job])})
        ci_tier['tier_tag'] = self.tier_tag
        result = {"tier": ci_tier}
        return dict(results=result)

    def format_job_name_result(self, job_name_result):
        """
        Formats single job name data into dictionary

        :param job_name_result -- list of single jenkins job queried data
        :returns -- Formatted single job data
        """
        formatted_data = []
        for single_job_result in job_name_result:
            formatted_data.append(dict(build_url=single_job_result['ref_url'].split('/console')[0],
                                       build_number=self.get_build_number_from_url(single_job_result['ref_url']),
                                       build_status=single_job_result['outcome']))
            if single_job_result['outcome'] == 'FAILED':
                self.tier_tag = False

        return formatted_data

    @staticmethod
    def get_build_number_from_url(job_build_url):
        """
        Method for parsing job build id from job build url

        :param job_build_url -- job build url containing job build id
        :returns -- job build id
        """
        splitted = job_build_url.split('/')
        if splitted[-1].isnumeric():
            return splitted[-1]
        elif splitted[-2].isnumeric():
            return splitted[-2]
        return "unknown"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Query data from resultsDB.'
    )
    parser.add_argument("job_names",
                        type=str,
                        nargs="*",
                        help="Jenkins job name")
    parser.add_argument("--resultsdb-api-url",
                        required=True,
                        help="Resultsdb api url from which job data will be queried.")
    parser.add_argument('--ca-bundle',
                        default='/etc/ssl/certs/ca-bundle.crt',
                        help="Certificate bundle to verify resultsdb api url")
    nvr = parser.add_mutually_exclusive_group(required=True)
    nvr.add_argument("--nvr",
                     type=str,
                     help="NVR of tested component")
    nvr.add_argument("--ci-message",
                     type=str,
                     help="Path to ci-message json file which contains nvr information")
    nvr.add_argument("--env-variable",
                     type=str,
                     help="Name of environmental variable which contain nvr information")
    parser.add_argument("--test-tier",
                        type=str,
                        required=True,
                        help="Tier of tested Jenkins job.")
    parser.add_argument('--output',
                        metavar='<output-metadata-file>',
                        default='metamorph.json',
                        help='Output metadata file name where CI Message data will be stored',
                        nargs='?')
    return parser.parse_args()


def get_nvr_information(args):
    """
    Function for parsing nvr information from given input
    return value is set to args.nvr and it will be changed in args object.

    :param args -- argparse object of parsed input variables
    """
    if args.ci_message:
        with open(args.ci_message) as ci_message:
            message_data = json.load(ci_message)
        args.nvr = "{0}-{1}-{2}".format(message_data['package'], message_data['version'], message_data['release'])
    elif args.env_variable:
        args.nvr = os.getenv(args.env_variable, "UNKNOWN")


def main():
    setup_logging(default_path="metamorph/etc/logging.json")
    logging.captureWarnings(True)
    args = parse_args()
    get_nvr_information(args)
    resultsdb = ResultsDBApi(args.job_names, args.nvr, args.test_tier, args.resultsdb_api_url, args.ca_bundle)
    resultsdb.get_test_tier_status_metadata()
    result = resultsdb.format_result()
    write_json_file(dict(resultsdb=result), args.output)


if __name__ == '__main__':
    main()
