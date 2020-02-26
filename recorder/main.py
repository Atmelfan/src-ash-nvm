import logging
import platform
import time

from common.common_csci import Csci, mqtt_proto
from common.proto.logging_pb2 import LogRecord
from common.proto.common_pb2 import Exit

import colorlog

from recorder.db_recorder import DbRecorder, DbRecordHandler


class RecorderCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='recorder')

        formatter = colorlog.ColoredFormatter('%(log_color)s%(asctime)s - %(name)s - %(topic)s : %(message)s')
        self.recorder = logging.getLogger("recorder-log")
        self.recorder.setLevel(self.args.record)
        self.logger.info("Logging level = %s", self.args.record)

        # Console logging handler
        ch = logging.StreamHandler()
        ch.setLevel(self.args.record)
        ch.setFormatter(formatter)
        self.recorder.addHandler(ch)

        # Recorder database
        self.data_log = DbRecorder('data', {
            'data': ['time integer', 'topic text', 'data blob'],
            'log': ['time integer', 'name text', 'level text', 'msg text']
        }, dir='records')

        # Console logging handler
        dh = DbRecordHandler(self.data_log)
        dh.setLevel(self.args.record)
        self.recorder.addHandler(dh)

    def setup_args(self):
        super().setup_args()
        rec_args = self.parser.add_argument_group('Log recorder')
        rec_args.add_argument('record', type=str, choices=logging._nameToLevel.keys(),
                              help='Logging level to record')

        dat_args = self.parser.add_argument_group('Data recorder')
        dat_args.add_argument('topics', type=str, nargs='*',
                              help='Topics to record. Note: \'log/#\', \'shutdown/#\' and \'command/#\' are never recorded')

    def shutdown(self):
        super().shutdown()
        self.mqtt.disconnect()
        if self.data_log:
            self.data_log.stop()

    def on_connect(self, client, user, flags, rc):
        super().on_connect(client, user, flags, rc)

        for topic in self.args.topics:
            self.logger.info("Recording topic '%s'" % topic)
            client.subscribe(topic)
            self.mqtt.message_callback_add(topic, self.on_data)

        # Listen to log messages
        client.subscribe("log/#")
        client.message_callback_add("log/#", self.on_log)

        # Listen to exit messages
        client.subscribe("shutdown/#")
        client.message_callback_add("shutdown/#", self.on_exit)

        # Subscribe on commands
        client.subscribe("command/#")
        self.mqtt.message_callback_add("command/#", self.on_command)

    def on_data(self, client, user, msg):
        self.recorder.debug("%s", msg.payload, extra={'topic': msg.topic})
        if self.data_log:
            self.data_log.record('data', (int(time.monotonic()*10e6), msg.topic, msg.payload))

    @mqtt_proto(LogRecord)
    def on_log(self, client, user, msg, rec):
        record = self.recorder.makeRecord(rec.name, rec.lvl, "", 0, rec.msg, [], "", extra={'topic': msg.topic})
        self.recorder.handle(record)

    def on_exit(self, client, user, msg):
        ex = Exit()
        ex.ParseFromString(msg.payload)
        if ex.reason == Exit.EXCEPTION:
            self.recorder.error("CSCI exception: %s", ex.msg, extra={'topic': msg.topic})
        elif ex.reason == Exit.KEYBOARD_INTERRUPT:
            self.recorder.error("CSCI interrupted: %s", ex.msg, extra={'topic': msg.topic})
        else:
            self.recorder.warning("CSCI exit: %s", ex.msg, extra={'topic': msg.topic})

    def on_command(self, client, user, msg):
        self.recorder.warning("Command: %s", str(msg.payload), extra={'topic': msg.topic})


if __name__ == '__main__':
    reco = RecorderCsci()
    reco.start()
