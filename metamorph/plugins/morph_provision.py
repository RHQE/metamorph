#!/usr/bin/python
import logging
import logging.config

from argparse import ArgumentParser, ArgumentError

from metamorph.lib.support_functions import setup_logging
from metamorph.metamorph_plugin import MetamorphPlugin

from git import Repo
from git.exc import GitCommandError


class ProvisionException(Exception):
    """Provision exception class"""
    pass


class Provision(MetamorphPlugin):
    """
    Class for openstack topology creation.
    Provide method for topology credentials creation.
    """
    provision_topology = {
        'topology_name': "unknown_topo",
        'site': "ci-osp",
        'resource_groups': dict
    }

    resource_groups = {
        'resource_group_name': "openstack",
        'res_group_type': "openstack",
        'credentials': {'profile': 'e2e-openstack', 'auth_type': ''},
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

    def __init__(self, git_repo, metadata, metadata_loc, osp_config, credentials_name):
        super().__init__()
        self.git_repo = git_repo
        self.metadata_file = metadata
        self.metadata_loc = metadata_loc
        self.osp_config = osp_config
        self.osp_data = dict
        self.credentials_name = credentials_name
        self.openstack_topology_credentials = dict()

    def get_provision_metadata(self):
        """
        Method for getting provision topology
        Credentials values are stored in openstack_topology_credentials parameter

        :returns tuple -- first elements is dictionary of provision topology and second dictionary
                          of topology credentials
        """
        self.clone_git_repository(self.git_repo)
        self.setup_topology_by_osp_config(self.osp_config)
        self.openstack_topology_credentials = self.get_openstack_credentials(self.osp_data)
        if self.metadata_file:
            self.setup_topology_by_metadata(self.metadata_file, self.metadata_loc)
        self.resource_groups['res_defs'] = self.res_defs
        self.provision_topology['resource_groups'] = self.resource_groups
        return self.provision_topology, self.openstack_topology_credentials

    def get_openstack_credentials(self, osp_data):
        """
        Static method for getting openstack credentials
        :param osp_data -- osp_config data

        :returns Credentials topology. Single key contains recommended credentials file name.
                 Key values are openstack credentials values
        """
        openstack_credentials = {'endpoint': osp_data['sites'][0]['endpoint'],
                                 'project': osp_data['sites'][0]['project'],
                                 'username': osp_data['sites'][0]['username'],
                                 'password': osp_data['sites'][0]['password']}
        if self.credentials_name == 'unknown_credentials.yaml':
            self.credentials_name = '{}_openstack.yaml'.format(
                osp_data['sites'][0]['project'].replace('-', '_'))
        self.resource_groups['credentials']['auth_type'] = 'file:{}'.format(self.credentials_name)
        return openstack_credentials

    def clone_git_repository(self, git_repo):
        """
        Method for cloning given repository

        :param git_repo -- git repository path
        """
        try:
            repo_name = self.get_git_repo_name(git_repo)
            Repo.clone_from(git_repo, repo_name)
        except GitCommandError as detail:
            logging.error('Error during cloning git repository "{0}"'.format(git_repo))
            raise ProvisionException("Error during cloning git "
                                     "repository {0} with detail: {1}".format(git_repo, detail))

    def setup_topology_by_osp_config(self, osp_config_path):
        """
        Method for actualizing topology values from osp config

        :param osp_config_path -- Path to osp config in cloned repository
        """
        try:
            self.osp_data = self.read_json_file(osp_config_path)
        except IOError:
            raise LookupError('OSP config file "{}" was not found. '
                              'Please check file path'.format(osp_config_path))
        self.res_defs['networks'] = self.osp_data['sites'][0]['networks']
        self.res_defs['keypair'] = self.osp_data['sites'][0]['keypair']
        self.res_defs['flavor'] = self.osp_data['resources'][0].get('flavor', 'm1.small')
        self.res_defs['count'] = self.osp_data['resources'][0].get('count', '1')
        self.res_defs['image'] = self.osp_data['resources'][0]['image']
        self.provision_topology['site'] = self.osp_data['sites'][0]['site']

    def setup_topology_by_metadata(self, metadata_path, metadata_location):
        """
        Method for actualizing topology values by provided yaml metadata file

        :param metadata_path -- Path to metadata file in cloned repository
        :param metadata_location -- Dictionary of searched metadata in given metadata file
        """
        try:
            metadata = self.read_yaml_file(metadata_path)
        except IOError:
            raise LookupError('Metadata file "{}" was not found. '
                              'Please check file path'.format(metadata_path))
        for metadata_name, location_value in metadata_location.items():
            try:
                extracted_data = self.get_metadata_from_location(metadata, location_value,
                                                                 location_value[-1])
            except KeyError as detail:
                raise ProvisionException('Unable to find key "{0}" in given path '
                                         '"{1}"'.format(detail, metadata_location[metadata_name]))
            self.update_topology_by_metadata(metadata_name, extracted_data)

    @staticmethod
    def get_correct_metadata_tree(metadata_source, metadata_location):
        """
        Method for getting correct metadata tree
        This method is need if metadata location contain list instead of dictionary.

        :param metadata_source -- Extracted metadata from metadata file
        :param metadata_location -- list which contains path to metadata

        :returns Dictionary of correct metadata by metadata location
        """
        for metadata_tree in metadata_source:
            if metadata_location[0] in metadata_tree.keys():
                return metadata_tree
        raise ProvisionException('Unable to find key "{}" in '
                                 'given metadata file'.format(metadata_location[0]))

    def update_topology_by_metadata(self, metadata_name, metadata_value):
        """
        Method for updating topology by metadata name and its value

        :param metadata_name -- topology metadata name
        :param metadata_value -- metadata name value
        """
        if metadata_name in self.res_defs.keys():
            self.res_defs[metadata_name] = metadata_value
            if metadata_name != 'networks':
                self.res_defs[metadata_name] = str(self.res_defs[metadata_name])
        elif metadata_name in self.resource_groups.keys():
            self.resource_groups[metadata_name] = str(metadata_value)
        elif metadata_name in self.provision_topology.keys():
            self.provision_topology[metadata_name] = str(metadata_value)
        else:
            raise ProvisionException('Unable to find given metadata name "{}". '
                                     'Name does not exists in topology file'.format(metadata_name))

    def get_metadata_from_location(self, metadata_source, metadata_location, metadata_name):
        """
        Method for getting metadata value from metadata file by it's path

        :param metadata_source -- extracted metadata from --metadata-file parameter
        :param metadata_location -- searching metadata location
        :param metadata_name -- name of metadata searched in given metadata location

        :returns found metadata
        """
        if isinstance(metadata_source, list):
            metadata_source = self.get_correct_metadata_tree(metadata_source, metadata_location)
        if metadata_name in metadata_source.keys():
            if isinstance(metadata_source[metadata_name], dict):
                raise ProvisionException("Metadata value can not be dictionary type. "
                                         "For more information see documentation.")
            return metadata_source[metadata_name]
        elif not metadata_source:
            raise ProvisionException('Unable to find metadata "{}" in given '
                                     'metadata location'.format(metadata_name))
        return self.get_metadata_from_location(metadata_source[metadata_location[0]],
                                               metadata_location[1:],
                                               metadata_name)

    @staticmethod
    def get_git_repo_name(git_repo):
        """
        Method for getting git repository name

        :param git_repo -- git repository path

        :returns repository name
        """
        git_repo = git_repo.rstrip('/')
        splitted_repo_path = git_repo.split('/')
        return splitted_repo_path[-1].split('.')[0]


def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(
        description='Prepare provisioning metadata.'
    )
    parser.add_argument("--git-repo",
                        type=str,
                        required=True,
                        help="Jenkins job name")
    parser.add_argument("--osp-config",
                        required=True,
                        help='Openstack stack sites default json file')
    metadata = parser.add_argument_group()
    metadata.add_argument("--metadata-file",
                          nargs='?',
                          help='Path to metadata yaml file in given git repository')
    metadata.add_argument("--metadata-loc", action='append',
                          type=lambda kv: kv.split("=", 1),
                          help='Metadata name with location. Usage --metadata-loc '
                               'metadata=path,to,metadata')
    parser.add_argument('--output-topology',
                        metavar='<output-topology-file>',
                        default='topology.yaml',
                        help='Name of topology file for provisioning',
                        nargs='?')
    parser.add_argument('--topology-credentials-name',
                        metavar='<output-topology-credentials-file>',
                        default='unknown_credentials.yaml',
                        help='Name of topology credentials for provisioning',
                        nargs='?')
    return parser.parse_args()


def setup_metadata_location_param(args):
    """
    Method for metadata location setup.
    They needs to be reformatted from list to dictionary

    :param args -- argparse object
    """
    location = dict()
    for single_mapping in args.metadata_loc:
        location[single_mapping[0]] = single_mapping[1].split(',')
    args.metadata_loc = location


def main():
    """Main function which manages plugin behavior"""
    setup_logging(default_path="metamorph/etc/logging.json")
    logging.captureWarnings(True)
    args = parse_args()
    if args.metadata_file and not args.metadata_loc:
        raise ArgumentError(None, "Argument error: '--metadata-file' "
                                  "must be provided with '--metadata-loc' argument")
    elif not args.metadata_file and args.metadata_loc:
        raise ArgumentError(None, "Argument error: '--metadata-loc' "
                                  "must be provided with '--metadata-file' argument")
    if args.metadata_file:  # Metadata location data must be
        setup_metadata_location_param(args)
    provisioning = Provision(args.git_repo, args.metadata_file, args.metadata_loc, args.osp_config,
                             args.topology_credentials_name)
    topology, topology_credentials = provisioning.get_provision_metadata()
    provisioning.write_yaml_file(topology, args.output_topology)
    provisioning.write_yaml_file(topology_credentials, provisioning.credentials_name)

if __name__ == '__main__':
    main()
