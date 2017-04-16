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


def storing_pretty_json(input_data, output="metamorph.json"):
    with open(output, "w") as metamorph:
        json.dump(input_data, metamorph, indent=2)
