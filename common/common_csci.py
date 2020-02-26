import argparse
import functools
import logging
import time

import paho.mqtt.client as mqtt

from .proto import common_pb2
from .mqtt_logger import MqttHandler


def mqtt_proto(message):
    """Deserializes a protobuf packet before calling the callback"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, client, user, msg):
            rec = message()
            rec.ParseFromString(msg.payload)
            func(self, client, user, msg, rec)
        return wrapper
    return decorator


class Csci(object):
    def __init__(self, name='named_no') -> None:
        super().__init__()
        self.name = name

        self.parser = argparse.ArgumentParser(description='Process some integers.', prog=name)

        mqtt_args = self.parser.add_argument_group('[COMMON] MQTT settings')
        mqtt_args.add_argument('--host', type=str, default="localhost", help='MQTT broker address')
        mqtt_args.add_argument('--port', type=int, default=1883, help='MQTT broker port')

        log_args = self.parser.add_argument_group('[COMMON] Logger settings')
        log_args.add_argument('--level', type=str, default='INFO', help='Logger level')
        log_args.add_argument('--log-no-mqtt', action='store_true', help='Log to MQTT')

        self.setup_args()

        # Read args
        self.args = self.parser.parse_args()

        # Setup MQTT
        self.mqtt = mqtt.Client()
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message
        self.mqtt.on_disconnect = self.on_disconnect

        # Setup logger
        self.logger = logging.getLogger(name)
        try:
            self.logger.setLevel(self.args.level)
        except KeyError:
            self.logger.error('Invalid logging level')

        # Console logging handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.NOTSET)
        self.logger.addHandler(ch)

        self.exit = False

        self.logger.debug("Connecting...")
        self.mqtt.connect(self.args.host, port=self.args.port)

        # MQTT logging handler
        mh = MqttHandler(self.mqtt, "log/%s/" % self.name)
        mh.setLevel(logging.NOTSET)
        if not self.args.log_no_mqtt:
            self.logger.addHandler(mh)
            self.logger.info("MQTT logging enabled")

        # Start main loop
        self.mqtt.loop_start()

    def setup_args(self):
        pass

    def get_sub_topic(self, sub):
        return self.name + '/' + sub

    def run(self):
        time.sleep(1)

    def start(self):
        exit_msg = common_pb2.Exit()
        exit_msg.msg = "()"
        exit_msg.reason = common_pb2.Exit.EXIT
        try:
            while not self.exit:
                self.run()
            self.mqtt.publish('shutdown/exit/' + self.name, payload=exit_msg.SerializeToString(), qos=2)

        except Exception as e:
            exit_msg.msg = str(e)
            exit_msg.reason = common_pb2.Exit.EXCEPTION
            self.mqtt.publish('shutdown/exception/' + self.name, payload=exit_msg.SerializeToString(), qos=2)
            self.logger.exception("Exception: %s", e)
        except KeyboardInterrupt:
            exit_msg.msg = 'interrupt'
            exit_msg.reason = common_pb2.Exit.KEYBOARD_INTERRUPT
            self.mqtt.publish('shutdown/interrupt/' + self.name, payload=exit_msg.SerializeToString(), qos=2)
            self.logger.warning("Keyboard interrupt!")
        finally:
            self.logger.info("Shutting down...")
            self.shutdown()
            self.mqtt.loop_stop()

    def shutdown(self):
        pass

    def on_command(self, client, user, msg):
        if msg.payload == b"shutdown":
            self.logger.warning("Received shutdown command")
            self.exit = True

    def on_connect(self, client, user, flags, rc):
        self.logger.info("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("#")

        # Subscribe on commands
        client.subscribe("command/*")
        client.subscribe("command/" + self.name)
        self.mqtt.message_callback_add("command/#", self.on_command)

    def on_disconnect(self, client, user, reasonCode, properties):
        client.reconnect()

    # The callback for when a PUBLISH message is received from the server.
    @staticmethod
    def on_message(client, self, msg):
        print(msg.topic + " " + str(msg.payload))




