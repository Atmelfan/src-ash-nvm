import os
import platform
import time

from common.common_csci import Csci

import psutil

from .proto.host_pb2 import CoreUsage, CoreFrequency


class HostCsci(Csci):

    def __init__(self) -> None:
        super().__init__(name='host/'+platform.uname()[1])

    def setup_args(self):
        super().setup_args()
        host_args = self.parser.add_argument_group('Host')
        host_args.add_argument('--watch', action='store_true',
                               help="Host is only allowed to watch the host, not act on it")
        host_args.add_argument('--tx2', action='store_true',
                               help="TX2 has extra temperature sensors not exposed through normal API")
        host_args.add_argument('--period', type=float, default=60.0,
                               help="Period to sample information with")

    def shutdown(self):
        super().shutdown()

    def run(self):
        self.logger.debug("Updating host statistics")
        self.update_cpu()
        self.update_memory()
        self.update_network()
        self.update_thermal()
        time.sleep(self.args.period)

    def update_cpu(self):
        frequencies = psutil.cpu_freq(percpu=True)
        for cpu, freq in enumerate(frequencies):
            self.mqtt.publish(self.get_sub_topic("cpu/%d/freq" % cpu), payload=str(freq.current))
        usages = psutil.cpu_percent(percpu=True)
        for cpu, usage in enumerate(usages):
            self.mqtt.publish(self.get_sub_topic("cpu/%d/usage" % cpu), payload=str(usage))
        load = [x / float(psutil.cpu_count()) * 100.0 for x in psutil.getloadavg()]
        self.mqtt.publish(self.get_sub_topic("load/1min"), payload=str(load[0]))
        self.mqtt.publish(self.get_sub_topic("load/5min"), payload=str(load[1]))
        self.mqtt.publish(self.get_sub_topic("load/15min"), payload=str(load[2]))

    def update_memory(self):
        mem = psutil.virtual_memory()
        self.mqtt.publish(self.get_sub_topic("mem/used"), payload=str(mem.used / 1024.0))
        self.mqtt.publish(self.get_sub_topic("mem/available"), payload=str(mem.available / 1024.0))
        self.mqtt.publish(self.get_sub_topic("mem/total"), payload=str(mem.total / 1024.0))

    def update_network(self):
        interfaces = psutil.net_io_counters(pernic=True)
        for interface, stats in interfaces.items():
            # Don't care about inactive interfaces
            if stats.bytes_sent == 0 and stats.bytes_recv == 0:
                continue
            self.mqtt.publish(self.get_sub_topic("net/%s/sent" % interface), payload=str(stats.bytes_sent))
            self.mqtt.publish(self.get_sub_topic("net/%s/recv" % interface), payload=str(stats.bytes_recv))

    @staticmethod
    def read_proc_value(path):
        with open(path) as proc_file:
            return [x for x in proc_file.readlines()]

    def read_ina3221(self, path, channel):
        name = self.read_proc_value(path + '/rail_name_%d' % channel)[0]
        return name, {
            'current': self.read_proc_value(path + '/in_current%d_input' % channel)[0],
            'voltage': self.read_proc_value(path + '/in_voltage%d_input' % channel)[0],
            'power': self.read_proc_value(path + '/in_power%d_input' % channel)[0]
        }

    def update_thermal(self):
        index = 0
        if self.args.tx2:
            # TX2 is weird

            # Thermal sensors
            sensors = ['/sys/class/thermal/thermal_zone0',
                       '/sys/class/thermal/thermal_zone1',
                       '/sys/class/thermal/thermal_zone2',
                       '/sys/class/thermal/thermal_zone3',
                       '/sys/class/thermal/thermal_zone4',
                       '/sys/class/thermal/thermal_zone5',
                       '/sys/class/thermal/thermal_zone6',
                       '/sys/class/thermal/thermal_zone7']
            thermal_zones = {self.read_proc_value(path+'/type')[0]: self.read_proc_value(path+'/temp') for path in sensors}
            for tz, value in thermal_zones.items():
                self.mqtt.publish(self.get_sub_topic("temp/%s/%s" % (tz.strip().lower(), 'temp')), payload=str(float(value[0])/1000.0))

            # Power monitoring
            ina3221s = ['/sys/bus/i2c/drivers/ina3221x/0-0041/iio_device',
                        '/sys/bus/i2c/drivers/ina3221x/0-0040/iio_device']
            for ina in ina3221s:
                for ch in range(0, 3):
                    rail, values = self.read_ina3221(ina, ch)
                    for meas, value in values.items():
                        self.mqtt.publish(self.get_sub_topic("rail/%s/%s" % (rail.strip().lower(), meas.strip())),
                                          payload=str(float(value) / 1000.0))

            # Fan speed
            fan_rpm = self.read_proc_value('/sys/devices/generic_pwm_tachometer/hwmon/hwmon1/rpm')[0]
            self.mqtt.publish(self.get_sub_topic("fan_rpm"), payload=float(fan_rpm))
        else:
            # Normal host
            sensors = psutil.sensors_temperatures()
            for sensor, temps in sensors.items():
                for temp in temps:
                    label = temp.label
                    if not label:
                        label = 't'+str(index)
                        index += 1
                    self.mqtt.publish(self.get_sub_topic("temp/%s/%s" % (sensor.strip().lower(), label.strip())), payload=str(temp.current))
            index = 0
            fan_controllers = psutil.sensors_fans()
            for controller, fans in fan_controllers.items():
                for fan in fans:
                    label = fan.label
                    if not label:
                        label = 'fan'+str(index)
                        index += 1
                    self.mqtt.publish(self.get_sub_topic("fan/%s/%s" % (controller, label)), payload=str(fan.current))


if __name__ == '__main__':
    host = HostCsci()
    host.start()
