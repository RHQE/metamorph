#!/usr/bin/python
import argparse
import logging
import logging.config
import requests
import json

from lib.logging_conf import setup_logging


class ResultsDBApiException(Exception):
    pass


class ResultsDBApi(object):

    RESULTSDB_API_URL_ENDING = "/results?"
    BASE_OPTIONS = "item={NVR}&CI_tier={ci_tier}"
    RESULTSDB_LIMITER = 10

    def __init__(self, job_names, component_nvr, test_tier, resultsdb_api_url):
        if not resultsdb_api_url.endswith(self.RESULTSDB_API_URL_ENDING):
            resultsdb_api_url += self.RESULTSDB_API_URL_ENDING
        self.resultsdb_api_url = resultsdb_api_url
        self.job_names = job_names
        self.component_nvr = component_nvr
        self.test_tier = test_tier
        self.job_names_result = {}
        self.tier_tag = True

    def get_resultsdb_data(self):
        if self.job_names:
            return self.get_job_names_result()
        else:
            return self.get_jobs_by_nvr_and_tier(self.RESULTSDB_LIMITER)

    @staticmethod
    def query_resultsdb(url, url_options=""):
        logging.debug("Running resultsbd API query with this url: {}".format(url + url_options))
        response = requests.get(url + url_options)
        if response.status_code >= 300:
            logging.error("ERROR: Unable to access resultsdb site.")
            raise ResultsDBApiException("ERROR: Unable to access resultsdb site.")
        return response.json()

    def get_job_names_result(self):
        for job_name in self.job_names:
            i = 0
            is_url = True
            while is_url is not None:
                options_url = self.BASE_OPTIONS.format(NVR=self.component_nvr, ci_tier=self.test_tier) + \
                    "&job_names={0}&page={1}".format(job_name, i)
                query_result = self.query_resultsdb(self.resultsdb_api_url, options_url)
                self.job_names_result[job_name] += query_result['data']
                is_url = query_result['next']
        return self.job_names_result

    def get_jobs_by_nvr_and_tier(self, limit=10):
        # TODO In future change options to BASE_OPTIONS
        options = self.BASE_OPTIONS.format(NVR=self.component_nvr, ci_tier=self.test_tier)
        url = self.resultsdb_api_url + options
        i = 0
        next_page = ""
        queried_data = []
        while next_page is not None and i < limit:
            response_data = self.query_resultsdb(url, "&page={}".format(i))
            i += 1
            next_page = response_data['next']
            queried_data += response_data['data']
        self.job_names_result = self.setup_output_data(queried_data)
        return self.job_names_result

    @staticmethod
    def setup_output_data(resultsdb_data):
        formatted_output = {}
        for single_job in resultsdb_data:
            formatted_output[single_job['job_names']] += single_job
        return formatted_output

    def store_results_in_json(self, output='metamorph.json'):
        ci_tier = dict(ci_tier=self.test_tier,
                       nvr=self.component_nvr,
                       job_name=[],
                       tier_tag=False)
        for single_job in self.job_names_result:
            ci_tier['job_name'].append({single_job: self.format_job_name_result(self.job_names_result[single_job])})
        ci_tier['tier_tag'] = self.tier_tag
        result = {"tier": ci_tier}
        with open(output, "w") as metamorph:
            json.dump(dict(result=result), metamorph, indent=2)

    def format_job_name_result(self, job_name_result):
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
    resultsdb.store_results_in_json(args.output)


if __name__ == '__main__':
    main()
