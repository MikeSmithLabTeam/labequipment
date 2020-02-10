from . import arduino
import time
import numpy as np

SHAKER_ARDUINO_ID = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_757353034313511092C1-if00"
SPEAKER_ARDUINO_ID = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Micro-if00"
BAUDRATE = 115200


class Shaker:

    def __init__(self):
        self.power = arduino.Arduino(
            port=SHAKER_ARDUINO_ID,
            rate=BAUDRATE,
            wait=False)
        self.power.flush()
        self.speaker = arduino.Arduino(
            port=SPEAKER_ARDUINO_ID,
            rate=BAUDRATE,
            wait=False)
        self.start_serial()

    def start_serial(self):
        message = self.switch_mode()
        if message == 'Serial control enabled.\r\n':
            print(message)
        elif message == 'Manual control enabled.\r\n':
            print('Send command again')
            message = self.switch_mode()
            print(message)
        else:
            print('Something may have gone wrong')
            print(message)

    def switch_mode(self):
        self.power.send_serial_line('x')
        time.sleep(0.1)
        lines = self.power.readlines(2)
        message = lines[1]
        return message

    def ramp(
            self,
            start,
            end,
            rate,
            step_size=1,
            record=False,
            stop_at_end=False):
        if end > start:
            values = np.arange(start, end + 1, 1*step_size)
        else:
            values = np.arange(start, end - 1, -1*step_size)
        self.init_duty(start) if record else self.change_duty(start)
        delay = 1/rate
        time.sleep(delay)
        for v in values:
            t = time.time()
            self.change_duty(v)
            interval = delay - time.time() + t
            if interval > 0:
                time.sleep(interval)
            else:
                print('Rate too high, timing will not be accurate')
        if stop_at_end:
            self.init_duty(0) if record else self.change_duty(0)
        else:
            self.init_duty(end) if record else self.change_duty(end)

    def init_duty(self, val):
        string = 'i{:03}'.format(val)
        self.power.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        _ = self.read_all()

    def change_duty(self, val):
        string = 'd{:03}'.format(val)
        self.power.send_serial_line(string)
        self.speaker.send_serial_line(string[1:])
        _ = self.read_all()

    def read_all(self):
        string = self.power.read_all()
        return string

    def quit(self):
        self.switch_mode()
        self.power.quit_serial()
        self.speaker.quit_serial()

if __name__ == "__main__":
    myshaker = Shaker()
