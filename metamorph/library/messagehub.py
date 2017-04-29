#!/usr/bin/python
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
---
module: messagehub
short_description: Get messages from message bus.
version_added: 2.3.0
author: Jiri Kulda (@Jurisak)
options:
  user:
    description:
      - Username to use to connect to the message bus.
      - Mutually exclusive with env-variable
    required: true

  password:
    description:
      - Password to use to connect to the message bus.
      - Mutually exclusive with env-variable
    required: true

  selector:
    description:
      - JMS selector for filtering messages.
      - Mutually exclusive with env-variable
    required: false

  host:
    description:
      - Message bus host.
      - Mutually exclusive with env-variable
    required: true

  port:
    description:
      - Message bus port.
      - Mutually exclusive with env-variable
    required: false
    default: 61613

  destination:
    description:
      - Message bus topic/subscription.
      - Mutually exclusive with env-variable
    required: false
    default: /topic/CI

  count:
    description:
      - Limit number of messages to catch.
      - Mutually exclusive with env-variable
    required: false
    default: 1

  env-variable:
    description:
      - Name of environmental variable which contains CI message in .json format.
      - Mutually exclusive with user, password, selector, host, port, destination and count
    required: true
    default: None

  output:
    description:
      - Output metadata file name where CI Message data will be stored.
    required: false
    default: metamorph.json
'''

EXAMPLES = '''
- name: Get single message from message bus
  messagehub:
    user: "..."
    password: "..."
    host: "..."
  register: result

- name: Get single message from environmental variable
  messagehub:
    env-variable: "..."
  register: result

- name: Get single message from environmental variable and store it into hello.json
  messagehub:
    env-variable: "..."
    output: "hello.json"
  register: result
'''

RETURN = '''
Error message:
    description: Received error message from message bus
    returned: Error
    type: dictionary
    sample: {"header": "...", "message": "Error description"}
CI message:
    description: CI messages from message bus
    returned: changed
    type: dictionary
    sample: {"messages": [...]}
'''


import stomp
import logging
import logging.config
import time
import os

from metamorph.lib.logging_conf import setup_logging
from metamorph.metamorph_plugin import MetamorphPlugin
from ansible.module_utils.basic import AnsibleModule


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


def messagebus_run(module):
    conn = stomp.Connection([(module.params['host'], module.params['port'])])
    listener = CIListener(module.params['count'])
    conn.set_listener('CI Listener', listener)
    conn.start()
    conn.connect(login=module.params['user'], passcode=module.params['password'], wait=True)
    if module.params['selector']:
        conn.subscribe(
            destination=module.params['destination'],
            id='1',
            ack='auto',
            headers={'selector': module.params['selector']}
        )
    else:
        conn.subscribe(
            destination=module.params['destination'],
            id='1',
            ack='auto'
        )
    logging.info("Connection to message bus established.")
    logging.info("Waiting for CI message to arrive ...")
    while (not listener.error_message) and len(listener.metamorph_data) < module.params['count']:
        logging.debug("Waiting 1s for CI message to arrive")
        time.sleep(1)
    conn.disconnect()
    return listener.error_message, listener.metamorph_data[:module.params['count']]


def main():
    messagebus = {
        "user": {"type": "str"},
        "password": {"type": "str"},
        "selector": {"type": "str"},
        "host": {"type": "str"},
        "port": {"default": 61613, "type": "int"},
        "destination": {"default": '/topic/CI', "type": "str"},
        "count": {"default": 1, "type": "int"},
        "env-variable": {"type": "str"},
        "output": {"type": "str", "default": "metamorph.json"}
    }
    mutually_exclusive = [
        ['env-variable', 'user'],
        ['env-variable', 'password'],
        ['env-variable', 'selector'],
        ['env-variable', 'host'],
        ['env-variable', 'port'],
        ['env-variable', 'destination'],
        ['env-variable', 'count']
    ]
    setup_logging(default_path="metamorph/etc/logging.json")
    module = AnsibleModule(argument_spec=messagebus, mutually_exclusive=mutually_exclusive)
    error_message = ""
    ci_message = ""
    if module.params['env-variable']:
        ci_message = os.environ.get(module.params['env-variable'], "UNKNOWN")
        if ci_message == "UNKNOWN":
            logging.error("Environmental variable not found")
            error_message = "Environmental variable not found"
    elif not (module.params['user'] and module.params['password'] and module.params['host']):
        module.fail_json(msg="Error in argument parsing. Arguments: user, password and host are required")
    else:
        error_message, ci_message = messagebus_run(module)

    if not error_message:
        MetamorphPlugin.storing_pretty_json(ci_message, module.params['output'])
        module.exit_json(changed=True, meta=dict(messages=ci_message))
    else:
        module.fail_json(msg="Error occurred in processing CI Message.", meta=error_message)


if __name__ == '__main__':
    main()
