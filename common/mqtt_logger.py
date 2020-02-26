from logging import LogRecord
from logging.handlers import QueueHandler

from .proto import logging_pb2


class MqttHandler(QueueHandler):
    def __init__(self, _mqtt, topic, *kvargs, **kwargs):
        super().__init__(None)
        self.mqtt = _mqtt
        self.topic = topic

    @staticmethod
    def on_connect(client, userdata, flags, reasonCode, properties):
        print("Connected!")

    @staticmethod
    def on_disconnect(client, userdata, reasonCode, properties):
        client.reconnect()

    def prepare(self, record: LogRecord):
        rec = logging_pb2.LogRecord()

        rec.name = record.name
        rec.msg = record.getMessage()
        rec.lvl = record.levelno

        return record.levelname, rec.SerializeToString()

    def enqueue(self, record: (str, logging_pb2.LogRecord)):
        self.mqtt.publish(self.topic + record[0], payload=record[1])

