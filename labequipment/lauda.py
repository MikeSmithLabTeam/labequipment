import time

import numpy as np
import serial


class Lauda(serial.Serial):

    def __init__(self, port):
        super().__init__(port)
        self.read_all()

    def read_current_temp(self):
        try:
            self.read_all()
            self.write(b'IN_PV_01\r\n')
            time.sleep(0.3)
            txt = self.read_all()
            val = float(txt)
        except:
            val = np.NaN
        return val

    def start(self):
        self.read_all()
        self.write(b'START\r\n')

    def stop(self):
        self.read_all()
        self.write(b'STOP\r\n')

    def set_temp(self, new_temp):
        self.read_all()
        self.write(bytes('OUT_SP_00_{:06.2f}\r\n'.format(new_temp),
                         encoding='utf-8', errors='strict'))

    def set_pumping_speed(self, val):
        self.read_all()
        self.write(bytes('OUT_SP_01_{:03d}\r\n'.format(val),
                         encoding='utf-8', errors='strict'))