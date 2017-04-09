#!/usr/bin/python
import argparse
import logging
import logging.config
import json
import time
import requests

from lib.logging_conf import setup_logging


class ResultsDBApiException(Exception):
    pass


class ResultsDBApi(object):
    """
    Class to communicate and process data with resultsDB
    """
    TIMEOUT_LIMIT = 7200  # Wait 2 hours maximally
    RESULTSDB_LIMITER = 10
    MINUTE = 60  # 60 seconds

    def __init__(self, job_names, component_nvr, test_tier, resultsdb_api_url):
        self.resultsdb_api_url = resultsdb_api_url
        self.job_names = job_names
        self.job_names_result = {}
        self.tier_tag = True
        self.url_options = {'CI_tier': test_tier, 'item': component_nvr}

    def get_test_tier_metadata(self):
        """
        Method get_resultsdb_data it's the main function from which data are received

        :returns -- dictionary where keys are job names and their values are list of queried data
        """
        if self.job_names:
            for job_name in self.job_names:
                self.job_names_result[job_name] = self.get_resultsdb_data(job_name)
            return self.job_names_result
        else:
            queried_data = self.get_resultsdb_data(limit=self.RESULTSDB_LIMITER)
            self.job_names_result = self.setup_output_data(queried_data)
            return self.job_names_result

    @staticmethod
    def query_resultsdb(url, url_options=dict):
        """
        This method queries resultsDB with given url and url_option variable

        :param url -- resultdb api url
        :param url_options -- dictionary of wanted options

        :returns -- Queried data
        """
        logging.debug('Running resultsbd API query with this url: {0} and options {1}'.format(url, url_options))
        response = requests.get(url, params=url_options)
        if response.status_code >= 300:
            logging.error("ERROR: Unable to access resultsdb site.")
            raise ResultsDBApiException("ERROR: Unable to access resultsdb site.")
        return response.json()

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
            self.url_options['job_names'] = job_name
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
        return queried_data

    @staticmethod
    def setup_output_data(resultsdb_data):
        """
        Method for setting up data from get_job_by_nvr_and_tier method.
        Data needs to be in dictionary where keys will be job names

        :param resultsdb_data -- data from get_job_by_nvr_and_tier
        :returns -- dictionary where keys are job names and their values are list of queried data
        """
        formatted_output = {}
        for single_job in resultsdb_data:
            formatted_output[single_job['job_names']] += single_job
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
        return dict(result=result)

    def format_job_name_result(self, job_name_result):
        """
        Format's single job name data into dictionary

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
                        default="https://url.corp.redhat.com/resultdb",
                        help="Resultsdb api url from which job data will be queried.")
    parser.add_argument("--nvr",
                        type=str,
                        required=True,
                        help="NVR of tested component")
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


def main():
    setup_logging(default_path="etc/logging.json")
    args = parse_args()
    resultsdb = ResultsDBApi(args.job_names, args.nvr, args.test_tier, args.resultsdb_api_url)
    resultsdb.get_resultsdb_data()
    result = resultsdb.format_result()
    with open(args.output, "w") as metamorph:
        json.dump(dict(result=result), metamorph, indent=2)


if __name__ == '__main__':
    main()
