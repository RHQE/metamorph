#!/usr/bin/python
import argparse
import logging
import logging.config
import requests
import json

from lib.logging_conf import setup_logging


class ResultsDBApi(object):

    RESULTSDB_API_URL = "https://resultsdb.host.prod.eng.bos.redhat.com/api/v2.0/results?"

    def __init__(self, job_name, component_nvr, test_tier):
        self.job_name = job_name
        self.component_nvr = component_nvr
        self.test_tier = test_tier
        self.job_names_result = {}

    def get_job_names_result(self):
        for job_name in self.job_name:
            options = "item={NVR}&job_name={job_name}&CI_tier={ci_tier}".format(NVR=self.component_nvr,
                                                                                job_name=job_name,
                                                                                ci_tier=self.test_tier)
            response = requests.get(self.RESULTSDB_API_URL + options)
            if response.status_code >= 300:
                logging.error("ERROR: Unable to access resultsdb site.")
            self.job_names_result[job_name] = response.json()
        return self.job_names_result

    def store_results_in_json(self, output='metamorph.json'):
        ci_tier = dict(ci_tier=self.test_tier,
                       nvr=self.component_nvr,
                       job_name=[],
                       tier_tag=False)
        for single_job in self.job_names_result:
            ci_tier['job_name'].append({single_job: self.format_job_name_result(self.job_names_result[single_job])})
        result = {"tier": ci_tier}
        with open(output, "w") as metamorph:
            json.dump(dict(result=result), metamorph, indent=2)

    def format_job_name_result(self, job_name_result):
        return dict(build_url=job_name_result['ref_url'].split('/console'),
                    build_number=self.get_build_number_from_url(job_name_result['ref_url']),
                    build_status=job_name_result['outcome'])

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
        description='Query data from resultdsDB.'
    )
    parser.add_argument("job_name",
                        type=str,
                        nargs="+",
                        help="Jenkins job name")
    parser.add_argument("NVR",
                        type=str,
                        help="NVR of tested component")
    parser.add_argument("test_tier",
                        type=str,
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
    resultsdb = ResultsDBApi(args.job_name, args.NVR, args.test_tier)
    resultsdb.get_job_names_result()
    resultsdb.store_results_in_json(args.output)


if __name__ == '__main__':
    main()
