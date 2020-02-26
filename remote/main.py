import time
from collections import deque

import evdev

from common.common_csci import Csci

from . import controller


class RemoteCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='remote')
        self.whitelist = [*self.args.whitelist]
        self.logger.info("Whitelisted controllers: %s", self.whitelist)

        self.controllers = []
        self.queued = deque([])
        self.active = None

    def setup_args(self):
        super().setup_args()
        rec_args = self.parser.add_argument_group('Log recorder')
        rec_args.add_argument('-w', '--whitelist', type=str, nargs='*',
                              help='Whitelist controller')

    def controller_request(self, ctl: controller.Controller):
        # Controller is currently active, release
        if ctl == self.active:
            self.controller_release(ctl)

        # If controller is a master, use immediately, otherwise put in queue
        if ctl.mode == controller.ControllerMode.MASTER:
            self.active = ctl
            self.active.reset_time()
        else:
            self.queued.append(ctl)

    def controller_release(self):
        # De-activate and use queued controller if any
        try:
            self.active = self.queued.popleft()
            self.active.reset_time()
        except IndexError:
            self.active = None

    def run(self):
        # Update all controllers


        # Update active controller
        if self.active:
            # Check if controller has any time left
            if not self.active.has_time_left():
                self.logger.info("Controller %s is out of time" % self.active)
                self.active = None
            # Check if controller is still connected
            if not self.active.is_connected():
                self.logger.info("Controller %s is not connected" % self.active)
                self.active = None

        else:
            self.controller_release()


if __name__ == '__main__':

    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    for device in devices:

        if "Sony Interactive Entertainment Wireless Controller" in device.name:
            print(device.fn, device.name, device.phys, device.leds(verbose=True))


    test = RemoteCsci()
    test.start()
