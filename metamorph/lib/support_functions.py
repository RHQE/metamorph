#!/usr/bin/python
import logging
import logging.config
import os.path
import json


class ExistingMetamorphMetadataException(Exception):
    pass


def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration
    :param default_path Default path to logging.json file
    :param default_level Level of logging
    :param env_key Environmental variable which contains logging configuration file path

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


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
            raise ExistingMetamorphMetadataException("ERROR: Wrong format of given '{}'. "
                                                     "'metamorph' must be root element".format(output))
    else:
        with open(output, "w") as metamorph:
            json.dump(dict(metamorph=input_data), metamorph, indent=2)


def read_json_file(input_file):
    with open(input_file, "r") as message:
        return json.load(message)
