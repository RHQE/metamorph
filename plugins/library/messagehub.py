#!/usr/bin/python
import stomp
import logging
import logging.config
from ansible.module_utils.basic import *


def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration

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
        "selector": {"required": False,  "type": "str"},
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
    while (not listener.error_message) and len(listener.metamorph_data) < module.params['count']:
        time.sleep(1)
    conn.disconnect()

    if not listener.error_message:
        module.exit_json(changed=True, meta=dict(messages=listener.metamorph_data))
    else:
        module.fail_json(msg="Error deleting repo", meta=listener.error_message)


if __name__ == '__main__':
    main()
