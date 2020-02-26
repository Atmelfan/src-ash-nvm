from enum import Enum


class ControllerMode(Enum):
    MASTER = 1
    SLAVE = 2


class Controller(object):
    def __init__(self, mode: ControllerMode, name, time_limit=0):
        super().__init__()
        self.name = name
        self.mode = mode
        self.time_limit = time_limit
        self.time = 0

    def reset_time(self):
        self.time = self.time_limit

    def has_time_left(self):
        return self.time > 0

    def is_connected(self):
        return True


