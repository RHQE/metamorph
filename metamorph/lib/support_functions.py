#!/usr/bin/python
import logging
import logging.config
import os
import json


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
    with open(output, "w") as metamorph:
        json.dump(dict(messages=input_data), metamorph, indent=2)


def read_json_file(input_file):
    with open(input_file, "r") as message:
        return json.load(message)