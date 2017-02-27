#!/usr/bin/python
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

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
    required: true

  password:
    description:
      - Password to use to connect to the message bus.
    required: true

  selector:
    description:
      - JMS selector for filtering messages.
    required: false

  host:
    description:
      - Message bus host.
    required: false
    default: ci-bus.lab.eng.rdu2.redhat.com

  port:
    description:
      - Message bus port.
    required: false
    default: 61613

  destination:
    description:
      - Message bus topic/subscription.
    required: false
    default: /topic/CI

  count:
    description:
      - Limit number of messages to catch.
    required: false
    default: 1
'''

EXAMPLES = '''
- name: Get single message from message bus
  messagehub:
    user: "..."
    password: "..."
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
import json
from ansible.module_utils.basic import AnsibleModule


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
    fields = {
        "user": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str"},
        "selector": {"required": False, "type": "str"},
        "host": {"default": 'ci-bus.lab.eng.rdu2.redhat.com', "type": "str"},
        "port": {"default": 61613, "type": "int"},
        "destination": {"default": '/topic/CI', "type": "str"},
        "count": {"default": 1, "type": "int"}
    }
    setup_logging(default_path="../../logging.json")
    module = AnsibleModule(argument_spec=fields)
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
    while (not listener.error_message) and len(listener.metamorph_data) < module.params['count']:
        logging.info("Waiting 1s for CI message to arrive")
        time.sleep(1)
    conn.disconnect()

    if not listener.error_message:
        module.exit_json(changed=True, meta=dict(messages=listener.metamorph_data))
    else:
        module.fail_json(msg="Error deleting repo", meta=listener.error_message)


if __name__ == '__main__':
    main()
