import time

from body.proto.attitude_pb2 import Attitude
from body.proto.gait_pb2 import GaitParameters, GaitStart, GaitStop
from common.common_csci import Csci, mqtt_proto

import serial

class ScpiComm(object):

    def __init__(self, port, baudrate) -> None:
        super().__init__()
        self.ser = serial


class BodyCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='body')
        try:
            self.carrier = ScpiComm(self.args.port, self.args.baudrate)
        except IOError as ioe:
            self.logger.error("Failed to create serial port", exc_info=ioe)

    @mqtt_proto(Attitude)
    def on_attitude(self, client, user, msg, attitude):
        pass

    @mqtt_proto(GaitParameters)
    def on_gait_params(self, client, user, msg, params):
        pass

    @mqtt_proto(GaitStart)
    def on_gait_start(self, client, user, msg, rec):
        pass

    @mqtt_proto(GaitStop)
    def on_gait_stop(self, client, user, msg, rec):
        pass

    def run(self):
        super().run()
        self.update_body()

    def setup_args(self):
        super().setup_args()
        host_args = self.parser.add_argument_group('Body')
        host_args.add_argument('port', action='store_true', type=str,
                               help="Serial port")
        host_args.add_argument('--baudrate', action='store_true', type=int, default=9600,
                               help="Serial port baud rate")

    def update_body(self):
        pass


if __name__ == '__main__':
    body = BodyCsci()
    body.start()
