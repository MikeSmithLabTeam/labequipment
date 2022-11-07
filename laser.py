import serial
import time

ventus_commands = {
    'control_mode':b'CONTROL=POWER\r',
    'default_power':b'STPOW=50\r',
    'set_power' : 'POWER=',
    'get_power' : b'POWER?\r',
    'psu_temp':b'PSUTEMP?\r',
    'laser_temp':b'LASTEMP?\r',
    'status':b'STATUS?\r',
    'store': b'WRITE',
    'serial_settings': {
        'port':'COM5',
        'baudrate':19200,
        'parity':serial.PARITY_NONE,
        'stopbits':serial.STOPBITS_ONE,
        }
    }



class Laser:
    """This Class controls the Ventus mpc6000 laser
    All commands are sent via serial

    Args:
        serial (_type_): _description_
    """

    def __init__(self, laser=None):
        """_summary_

        Args:
            port (str, optional): _description_. Defaults to 'COM1'.
            baud_rate (int, optional): _description_. Defaults to 19200.
            parity (_type_, optional): _description_. Defaults to None.
            laser (_type_, optional): _description_. Supply dictionary of laser's commands
        """
        self.laser = laser
        serial_settings = laser['serial_settings']
        self.com = serial.Serial(
                port=serial_settings['port'],
                baudrate=serial_settings['baudrate'],
                parity=serial_settings['parity'],
                stopbits=serial_settings['stopbits']
                )
        self.com.timeout=5
        #self.com.write(self.laser['control_mode'])
        #time.sleep(1)
        #self.com.write(self.laser['store'])
        #time.sleep(1)
        #self.com.write(self.laser['default_power'])
        #time.sleep(1)
        #self.com.write(self.laser['store'])
        #print(self.com.readline())

    def _write(self, command, value=None):
        if value is None:
            msg = command + '\r\n'
        else:
            msg = command + str(value) + '\r\n'
            self.com.write(msg.encode('utf-8'))

    def _read(self):
        return self.com.readline().decode('utf-8').strip('\r\n')

    def set_power(self, power):
        self._write(self.laser['set_power'], power)

    def get_status(self):
        status = {}
        self.com.write(self.laser['status'])
        status['status']= self._read()
        self.com.write(self.laser['psu_temp'])
        status['T_psu']= self._read()
        self.com.write(self.laser['laser_temp'])
        status['T_laser']= self._read()
        self.com.write(self.laser['get_power'])
        status['power_mw']= self._read()
        return status

if __name__ == '__main__':
    laser = Laser(laser=ventus_commands)
    laser.set_power(60)
    #status=laser.get_status()

    #print(status)


