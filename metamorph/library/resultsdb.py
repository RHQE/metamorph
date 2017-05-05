#!/usr/bin/python
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
---
module: resultsdb
short_description: Get test tier status information from resultsdb.
version_added: 2.3.0
author: Jiri Kulda (@Jurisak)
options:
  job_names:
    description:
      - CI job names.
    required: false

  test_tier:
    description:
      - Number which specifies tested tier.
    required: true

  nvr:
    description:
      - Tested component in NVR format.
      - Mutually exclusive with env_variable and ci_message
    required: true

  ci_message:
    description:
      - Path to ci_message which contains NVR values.
      - Mutually exclusive with env_variable and nvr
    required: true

  env_variable:
    description:
      - Environmental variable which contains component in NVR format.
      - Mutually exclusive with nvr and ci_message
    required: true

  output:
    description:
      - Output metadata file name where test tier status information will be stored.
    required: false
    default: metamorph.json

  resultsdb_api_url:
    description:
      - Results api url of resultsDB
    required: true

  ca_bundle:
    description:
      - Path to certificate which verifies resultsDB api url.
    required: false
    default: /etc/ssl/certs/ca-bundle.crt
'''

EXAMPLES = '''
- name: Get test tier status by job names
  resultsdb:
    test_tier: 1
    nvr: "component-version-release"
    job_names: "..."
    resultsdb_api_url: "..."
  register: result

- name: Get test tier status by test tier and nvr
  resultsdb:
    test_tier: 1
    nvr: "component-version-release"
    resultsdb_api_url: "..."
  register: result

- name: Get test tier status by test tier, env_variable and store it into hello.json
  resultsdb:
    test_tier: 1
    env_variable: "SOME_VAR"
    output: "hello.json"
    resultsdb_api_url: "..."
  register: result
'''

RETURN = '''
Error message:
    description: An error from resultsdb class
    returned: Error
    type: dictionary
    sample: {"header": "...", "message": "Error description"}
Test tier status message:
    description: Test tier status information from resultsdb
    returned: changed
    type: dictionary
    sample: {"result": [...]}
'''

import logging
import logging.config
import json
import time
import os

import requests

from metamorph.lib.support_functions import setup_logging
from ansible.module_utils.basic import AnsibleModule


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
        if self.TIMEOUT_LIMIT == 0:
            raise ResultsDBApiException("Timeout limit reached and no data were queried.")
        return queried_data

    @staticmethod
    def setup_output_data(resultsdb_data):
        """
        Method for setting up data from get_job_by_nvr_and_tier method.
        Data needs to be in dictionary where keys will be job names

        :param resultsdb_data -- data which were queried without job_names option
        :returns -- dictionary where keys are job names and their values are list of queried data
        """
        formatted_output = {}
        for single_job in resultsdb_data:
            job_names_key = single_job['data'].get('job_names', ['UNKNOWN'])[0]
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


def get_nvr_information(module):
    """
    Function for parsing nvr information from given input
    return value is set to args.nvr and it will be changed in args object.

    :param module -- argparse object of parsed input variables
    """
    if module.params['ci_message']:
        with open(module.params['ci_message']) as ci_message:
            message_data = json.load(ci_message)
        module.params['nvr'] = "{0}-{1}-{2}".format(message_data['package'],
                                                    message_data['version'],
                                                    message_data['release'])
    elif module.params['env_variable']:
        module.params['nvr'] = os.getenv(module.params['env_variable'], "UNKNOWN")


def main():
    argument_spec = dict(
        job_names=dict(type='list', nargs='*'),
        resultsdb_api_url=dict(required=True, type='str'),
        nvr=dict(type='str'),
        ci_message=dict(type='str'),
        env_variable=dict(type='str'),
        test_tier=dict(type='int', required=True),
        output=dict(default='metamorph.json', type='str'),
        ca_bundle=dict(default='/etc/ssl/certs/ca-bundle.crt', type='str')
    )
    mutually_exclusive = [
        ['nvr', 'ci_message'],
        ['nvr', 'env_variable'],
        ['ci_message', 'env_variable'],
    ]
    setup_logging(default_path="./etc/logging.json")
    module = AnsibleModule(argument_spec=argument_spec, mutually_exclusive=mutually_exclusive)
    if not (module.params['nvr'] or module.params['ci_message'] or module.params['env_variable']):
        module.fail_json(msg="Error in argument parsing. One of (nvr, ci_message, env_variable) is required")
    get_nvr_information(module)
    resultsdb = ResultsDBApi(module.params['job_names'],
                             module.params['nvr'],
                             module.params['test_tier'],
                             module.params['resultsdb_api_url'],
                             module.params['ca_bundle'])
    resultsdb.get_test_tier_status_metadata()
    result = resultsdb.format_result()
    with open(module.params['output'], "w") as metamorph:
        json.dump(dict(result), metamorph, indent=2)
    module.exit_json(changed=True, meta=dict(result))

if __name__ == '__main__':
    main()
