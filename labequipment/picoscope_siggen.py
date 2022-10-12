
from picosdk.ps2000 import ps2000
from time import time_ns, sleep
from ctypes import byref, c_byte, POINTER, c_int16, c_int32, c_float, c_uint32, sizeof

class PicoScopeSigGen:

    """
    PicoScopeDAQ is a simple python interface to collect data from the picoscope 2000 series. 

    Installation: To run this code you need to download and install the drivers. 
    https://www.picotech.com/downloads. 
    You want 64bit PicoSDK. Once you've installed this then you can 
    pip install this code:
    "pip install git+https://github.com/MikeSmithLabTeam/labequipment"

    Useful additional info for programming is found
    here: https://www.picotech.com/download/manuals/ps2000pg.en-10.pdf
    
    
    """
    def __init__(self):
        """This assumes only one device connected to system. Checks device found and instantiates object"""
        self.device = ps2000.open_unit()
        print('Device info: {}'.format(self.device.info))
        
    
    def start(self, run_time=0, offset_voltage=0, pk_to_pk_voltage=0, wavetype='sine', freq=100):
        """
        If run_time = 0 signal generates indefinitely until stop called

        """
        wavetypes = {
                    'sine':0, 
                    'square':1, 
                    'triangle':2,
                    'dc':5
                    }

        assert wavetype in wavetypes.keys(), 'Unrecognised wavetype'


        ps2000.ps2000_set_sig_gen_built_in(self.device.handle, c_int32(offset_voltage), c_uint32(pk_to_pk_voltage), wavetypes[wavetype], c_float(freq), c_float(freq), c_float(0.0), c_float(0.0),2,c_uint32(0))
        
        start_time = time_ns()
        while (time_ns() - start_time < run_time*1E9) or ~run_time:
            sleep(0.01)


if __name__  == '__main__':
    pico = PicoScopeSigGen()
    pico.start(pk_to_pk_voltage=2)