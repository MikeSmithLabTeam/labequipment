import serial
import time
import os


class Arduino:

    def __init__(self, settings, timeout=0):
        """Open the selected serial port
        
        inputs:
        settings    :   Dict containing port and optionally rate
                        like:
                        {PORT   :   "COM1",
                        BAUDRATE    :  9600}
        
        If not supplying a value provide False.

        Use with context manager:
        
        Example: 

        with Arduino(settings) as ard:
            Do stuff.
                
        """
        self.port = serial.Serial(port=settings['PORT'], baudrate=settings['BAUDRATE'], timeout=timeout)
        time.sleep(1.5) #allowing time for serial port to reset.
        self.flush()
            
    def flush(self):
        '''
        Clears the buffer.        
        '''
        while self.port.in_waiting() > 1:
            self.port.reset_input_buffer()
        while self.port.out_waiting() > 1:
            self.port.reset_output_buffer()
      
    def choose_port(self, os='linux'):
        if os == 'linux':
            self.port.port = fd.load_filename(
                'Choose a comport',
                directory='/dev/')

    def send_serial_line(self, text):
        """
        Send a string over the serial port making sure it ends in a new
        line .

        Input:
            text    the string to be sent to the arduino
        """
        self.flush()
        if text[-2:] != "\n":
            text += "\n"
        text_in_bytes = bytes(text, 'utf8')
        self.port.write(text_in_bytes)

    def read_serial_bytes(self, no_of_bytes):
        """ Read a given no_of_bytes from the serial port"""
        size_of_input_buffer = 0
        while size_of_input_buffer < no_of_bytes:
            size_of_input_buffer = self.port.inWaiting()
        text = self.port.read(no_of_bytes)
        print(text.decode())

    def read_serial_line(self):
        """
        Waits for data in the input buffer then
        reads a single line from the serial port.

        Outputs:
            text    the data from serial in unicode
        """
        size_of_input_buffer = 0
        while size_of_input_buffer == 0:
            size_of_input_buffer = self.port.inWaiting()
            time.sleep(0.1)
        text = self.port.readline()
        return text.decode()

    def readlines(self, n):
        out = [self.port.readline().decode() for i in range(n)]
        return out

    def ignorelines(self, n):
        [self.port.readline() for i in range(n)]

    def read_all(self):
        string = ''
        while self.port.inWaiting() > 1:
            l = self.port.readline()
            string += l.decode("utf-8")
        return string

    def quit_serial(self):
        """ Close the serial port """
        self.port.close()
        print('port closed')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.quit_serial()
        
def find_port():
    items = os.listdir('/dev/')
    newlist = []
    for names in items:
        if names.startswith("ttyA"):
            newlist.append(names)
    return newlist[0].port.isOpen()