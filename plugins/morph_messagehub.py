#!/usr/bin/python
import logging
import logging.config
import os
import argparse
import time
import stomp
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Subscribe to CI message bus.'
    )
    parser.add_argument(
        '--user',
        dest='user',
        metavar='<user>',
        required=True,
        help='Username to use to connect to the message bus.'
    )
    parser.add_argument(
        '--password',
        dest='password',
        metavar='<password>',
        required=True,
        help='Password to use to connect to the message bus.'
    )
    parser.add_argument(
        '--selector',
        dest='selector',
        metavar='<JMS selector>',
        help='JMS selector for filtering messages.'
    )
    parser.add_argument(
        '--host',
        dest='host',
        metavar='<host>',
        required=True,
        help='Message bus host.'
    )
    parser.add_argument(
        '--port',
        dest='port',
        metavar='<port>',
        type=int,
        default=61613,
        help='Message bus port.'
    )
    parser.add_argument(
        '--destination',
        dest='destination',
        metavar='<destination>',
        default='/topic/CI',
        help='Message bus topic/subscription.'
    )
    parser.add_argument(
        '--count',
        dest='count',
        metavar='<count>',
        type=int,
        default=1,
        help='Limit number of messages to catch.'
    )
    return parser.parse_args()


class CIListener(stomp.ConnectionListener):
    def __init__(self, count):
        self.count = count
        self.metamorph_data = []
        self.error_message = {}

    def on_error(self, headers, message):
        self.error_message['headers'] = headers
        self.error_message['message'] = message

    def on_message(self, headers, message):
        if self.count > len(self.metamorph_data):
            self.metamorph_data.append({"header": headers, "message": message})
            self.count += 1


def main():
    setup_logging(default_path="../logging.json")
    args = parse_args()
    conn = stomp.Connection([(args.host, args.port)])
    listener = CIListener(args.count)
    conn.set_listener('CI Listener', listener)
    conn.start()
    conn.connect(login=args.user, passcode=args.password)
    if args.selector:
        conn.subscribe(
            destination=args.destination,
            id='1',
            ack='auto',
            headers={'selector': args.selector}
        )
    else:
        conn.subscribe(
            destination=args.destination,
            id='1',
            ack='auto'
        )
    logging.info("Connection to message bus established.")
    while (not listener.error_message) and len(listener.metamorph_data) < args.count:
        logging.info("Waiting 1s for CI message to arrive")
        time.sleep(1)
    conn.disconnect()
    if listener.error_message:
        exit("Got error message through message bus {0}".format(listener.error_message))
    with open("metamorph.json", "w") as metamorph:
        json.dump(dict(messages=listener.metamorph_data), metamorph, indent=2)

if __name__ == '__main__':
    main()
