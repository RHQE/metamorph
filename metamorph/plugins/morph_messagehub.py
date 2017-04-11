#!/usr/bin/python
import argparse
import logging
import logging.config
import time
import os
import stomp

from metamorph.lib.support_functions import setup_logging, write_json_file


def messagebus_run(args):
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
    logging.info("Waiting for CI message to arrive ...")
    while (not listener.error_message) and len(listener.metamorph_data) < args.count:
        logging.debug("Waiting 1s for CI message to arrive")
        time.sleep(1)
    conn.disconnect()
    if listener.error_message:
        exit("Got error message through message bus {0}".format(listener.error_message))
    write_json_file(listener.metamorph_data[:args.count], args.output)


def env_run(args):
    env_data = os.environ.get(args.env_variable, "UNKNOWN")
    if env_data == "UNKNOWN":
        logging.error("Environmental variable not found")
        exit(1)
    write_json_file(env_data, args.output)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Subscribe to CI message bus.'
    )
    subparser = parser.add_subparsers()
    env = subparser.add_parser('env')
    messagebus = subparser.add_parser('message')
    messagebus.add_argument(
        '--user',
        dest='user',
        metavar='<user>',
        required=True,
        help='Username to use to connect to the message bus.'
    )
    messagebus.add_argument(
        '--password',
        dest='password',
        metavar='<password>',
        required=True,
        help='Password to use to connect to the message bus.'
    )
    messagebus.add_argument(
        '--selector',
        dest='selector',
        metavar='<JMS selector>',
        help='JMS selector for filtering messages.'
    )
    messagebus.add_argument(
        '--host',
        dest='host',
        metavar='<host>',
        required=True,
        help='Message bus host.'
    )
    messagebus.add_argument(
        '--port',
        dest='port',
        metavar='<port>',
        type=int,
        default=61613,
        help='Message bus port.'
    )
    messagebus.add_argument(
        '--destination',
        dest='destination',
        metavar='<destination>',
        default='/topic/CI',
        help='Message bus topic/subscription.'
    )
    messagebus.add_argument(
        '--count',
        dest='count',
        metavar='<count>',
        type=int,
        default=1,
        help='Limit number of messages to catch.'
    )
    messagebus.add_argument(
        '--output',
        metavar='<output-metadata-file>',
        default='metamorph.json',
        help='Output metadata file name where CI Message data will be stored',
        nargs='?')
    messagebus.set_defaults(func=messagebus_run)
    env.add_argument(
        '--env-variable',
        metavar='<env-variable>',
        type=str,
        required=True,
        help="Name of environmental variable which contains CI message in .json format."
    )
    env.add_argument(
        '--output',
        metavar='<output-metadata-file>',
        default='metamorph.json',
        help='Output metadata file name where CI Message data will be stored',
        nargs='?')
    env.set_defaults(func=env_run)
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
            self.count += 1
            self.metamorph_data.append({"header": headers, "message": message})


def main():
    setup_logging(default_path="metamorph/etc/logging.json")
    args = parse_args()
    try:
        args.func(args)
    except Exception as exc:
        if "\'Namespace\' object has no attribute \'func\'".startswith(exc.__str__()):
            logging.warning("You need to specify input. Please run: \"morph_messagehub.py --help\" "
                            "for more information")
        else:
            logging.error("Error with function parsing. If this is a bug make an issue in github repo.\n "
                          "Message: {0}".format(exc))
            exit(1)

if __name__ == '__main__':
    main()
