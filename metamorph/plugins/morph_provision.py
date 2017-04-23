#!/usr/bin/python
import argparse
import logging
import logging.config
import json
import yaml

from git import Repo
from git.exc import GitCommandError
from metamorph.lib.logging_conf import setup_logging, storing_pretty_json


class ProvisionException(Exception):
    pass


class Provision(object):
    provision_topology = {
        'topology_name': "unknown_topo",
        'site': "ci-osp",
        'resource_groups': dict
    }

    resource_groups = {
        'resource_group_name': "openstack",
        'res_group_type': "openstack",
        'assoc_creds': '',
        'res_defs': dict
    }

    res_defs = {
        'res_name': "unknown_inst",
        'flavor': "m1.small",
        'res_type': "os_server",
        'image': "",
        'count': '1',
        'keypair': "",
        'networks': []
    }

    def __init__(self, git_repo, metadata, osp_config, test_suite):
        self.git_repo = git_repo
        self.metadata_file = metadata
        self.osp_config = osp_config
        self.test_suite = test_suite
        self.cloned_repo = None

    def get_provision_metadata(self):
        self.clone_git_repository(self.git_repo)
        self.setup_topology_by_metadata(self.metadata_file)
        self.setup_topology_by_osp_config(self.osp_config)
        self.resource_groups['res_defs'] = self.res_defs
        self.provision_topology['resource_groups'] = self.resource_groups
        return self.provision_topology

    def clone_git_repository(self, git_repo):
        try:
            repo_name = self.get_git_repo_name(git_repo)
            self.cloned_repo = Repo.clone_from(git_repo, repo_name)
        except GitCommandError as detail:
            logging.error('Error during cloning git repository "{0}"'.format(git_repo))
            raise ProvisionException("Error during cloning git repository {0} with detail: {1}".format(git_repo,
                                                                                                       detail))

    def setup_topology_by_osp_config(self, osp_config_path):
        with open(osp_config_path) as osp_config:
            osp_data = json.load(osp_config)
        self.res_defs['networks'] = osp_data['sites'][0]['networks']
        self.res_defs['keypair'] = osp_data['sites'][0]['keypair']
        self.res_defs['flavor'] = osp_data['resources'][0].get('flavor', 'm1.small')
        self.res_defs['count'] = osp_data['resources'][0].get('count', '1')
        self.res_defs['image'] = osp_data['resources'][0]['image']
        self.provision_topology['site'] = osp_data['sites'][0]['site']

    def setup_topology_by_metadata(self, metadata_path):
        with open(metadata_path) as metadata_fp:
            metadata = yaml.load(metadata_fp)
        print(metadata)

    @staticmethod
    def get_git_repo_name(git_repo):
        if git_repo.endswith('/'):
            git_repo = git_repo[:-1]
        splitted_repo_path = git_repo.split('/')
        return splitted_repo_path[-1].split('.')[0]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Prepare provisioning metadata.'
    )
    parser.add_argument("--git-repo",
                        type=str,
                        required=True,
                        help="Jenkins job name")
    parser.add_argument("--metadata-file",
                        required=True,
                        help='Path to metadata yaml file in given git repository')
    parser.add_argument("--osp-config",
                        required=True,
                        help='Openstack stack sites default json file')
    parser.add_argument("--test-suite",
                        nargs='?',
                        help='Name of test suite')
    parser.add_argument('--output-metadata',
                        metavar='<output-metadata-file>',
                        default='metamorph.json',
                        help='Output metadata file name where provision metadata will be stored',
                        nargs='?')
    parser.add_argument('--output-topology',
                        metavar='<output-topology-file>',
                        default='topology.yaml',
                        help='Name of topology file for provisioning',
                        nargs='?')
    return parser.parse_args()


def main():
    setup_logging(default_path="metamorph/etc/logging.json")
    logging.captureWarnings(True)
    args = parse_args()
    provisioning = Provision(args.git_repo, args.metadata_file, args.osp_config, args.test_suite)
    topology = provisioning.get_provision_metadata()
    storing_pretty_json(topology, args.output_topology)


if __name__ == '__main__':
    main()
