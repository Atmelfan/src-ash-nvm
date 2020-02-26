import time

from body.proto.attitude_pb2 import Attitude
from body.proto.gait_pb2 import GaitParameters, GaitStart, GaitStop
from common.common_csci import Csci, mqtt_proto


class BodyCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='body')

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

    def update_body(self):
        pass


if __name__ == '__main__':
    body = BodyCsci()
    body.start()
