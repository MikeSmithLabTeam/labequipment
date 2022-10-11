
from ctypes import byref, c_byte, c_int16, c_int32, c_float, sizeof
from time import sleep

from picosdk.ps2000 import ps2000
from picosdk.functions import assert_pico2000_ok, adc2mV, mV2adc
from picosdk.PicoDeviceEnums import picoEnum

import matplotlib.pyplot as plt
import numpy as np



def get_timebase(device, samples, wanted_time_interval, oversample=1):
    current_timebase = 1

    old_time_interval = None
    time_interval = c_int32(0)
    time_units = c_int16()
    max_samples = c_int32()

    while ps2000.ps2000_get_timebase(
        device.handle,
        current_timebase,
        samples,
        byref(time_interval),
        byref(time_units),
        oversample,
        byref(max_samples)) == 0 \
        or time_interval.value < wanted_time_interval:

        current_timebase += 1
        old_time_interval = time_interval.value

        if current_timebase.bit_length() > sizeof(c_int16) * 8:
            raise Exception('No appropriate timebase was identifiable')

    return current_timebase - 1, old_time_interval, time_units



class PicoScopeDAQ:

    def __init__(self):
        """This assumes only one device connected to system. Checks device found and instantiates object"""
        self.device = ps2000.open_unit()
        print('Device info: {}'.format(self.device.info))
        self.channel_a=None
        self.channel_b=None

    def setup_channel(self, channel='A', samples=8000, sample_rate=100000, coupling='DC', voltage_range=2, oversampling=1):
        """
        Channel can be 'A' or 'B' 
        samples - max depends on device and also on how many channels are used. 
        
                Model 2204a has 8kS - 1 channel = 8000 but 2 channels ~ 3965 samples,
        
        sample_rate - max depends on device. The actual sample rate is calculated and chosen to be the nearest available value
                    You can access this by calling self.
        Device range can be 0.05,0.1,0.2,0.5,1,2,5,10,20V 
        coupling can take values 'DC' or 'AC'
        """

        self.voltage_unit = 'V'
        if voltage_range < 1:
            self.voltage_unit = 'MV'
            voltage_range = int(voltage_range*1000)
        else:
            voltage_range = int(voltage_range)

        self._v_range=ps2000.PS2000_VOLTAGE_RANGE['PS2000_' + str(voltage_range) + self.voltage_unit]

        self.samples=samples
        self.sample_rate = sample_rate
        self.oversampling=oversampling
    
        if coupling == 'DC':
            coupling_id=1
        else:
            coupling_id=0
        
        channel_A=0
        channel_B=1

        if channel == 'A':     
            ps2000._python_set_channel(self.device.handle,channel_A, 1,coupling_id,self._v_range,None)
            if self.channel_b == None:
                ps2000._python_set_channel(self.device.handle,channel_B, 0,coupling_id,self._v_range,None) 
        elif channel == 'B':
            ps2000._python_set_channel(self.device.handle,channel_B, 1,coupling_id,self._v_range,None)
            if self.channel_a == None:
                ps2000._python_set_channel(self.device.handle,channel_A, 0,coupling_id,self._v_range,None) 
        self.timebase, self.interval, self.time_units = get_timebase(self.device, samples, 1E9/sample_rate, oversample=oversampling)
        

    def setup_trigger(self,channel='A', threshold=0, direction=0,  delay=0):
        """
        This is optional and if not called the data will collect immediately

        channel - specifies channel on which trigger acts
        threshold - value at which trigger is activated
        direction - 0=rising, 1=falling
        delay - Some weird definition relating trigger to start of data gathering in %. Read the manual and see if you understand.
        """
        if channel=='A':
            channel_id = 0
        elif channel=='B':
            channel_id=1

        #Convert threshold
        millivolts = threshold*1000
        converted_threshold = mV2adc(millivolts, self._v_range, c_int16(32767))

        ps2000.ps2000_set_trigger(c_int16(self.device.handle), c_int16(channel_id), c_int16(converted_threshold), c_int16(direction), c_int16(delay), c_int16(0))

    def start(self, channel='A'):
        "Options are 'A', 'B' or 'BOTH'"
        channel_a_v, channel_b_v = None, None


        collection_time = c_int32()

        res = ps2000.ps2000_run_block(
            self.device.handle,
            self.samples,
            self.timebase,
            self.oversampling,
            byref(collection_time)
        )

        while ps2000.ps2000_ready(self.device.handle) == 0:
            sleep(0.1)

        times = (c_int32 * self.samples)()
        if (channel == 'A') or (channel == 'BOTH'):
            buffer_a = (c_int16 * self.samples)()
        if (channel == 'B') or (channel == 'BOTH'):
            buffer_b = (c_int16 * self.samples)()
         
        overflow = c_byte(0)

        if channel == 'BOTH':
            res = ps2000.ps2000_get_times_and_values(
                self.device.handle,
                byref(times),
                byref(buffer_a),
                byref(buffer_b),
                None,
                None,
                byref(overflow),
                self.time_units,  
                self.samples,
                )
            channel_a_v = np.array(adc2mV(buffer_a, self._v_range, c_int16(32767)))/1000 # convert from mV to V
            channel_b_v = np.array(adc2mV(buffer_b, self._v_range, c_int16(32767)))/1000   
        elif channel == 'A':
            res = ps2000.ps2000_get_times_and_values(
                self.device.handle,
                byref(times),
                byref(buffer_a),
                None,
                None,
                None,
                byref(overflow),
                self.time_units,  
                self.samples,
                )
            channel_a_v = np.array(adc2mV(buffer_a, self._v_range, c_int16(32767)))/1000 # convert from mV to V
               

        times=np.array(times[:])/1E9 # Convert from ns to s
           
        return times, channel_a_v, channel_b_v
    
    def close_scope(self):
        ps2000.ps2000_close_unit(self.device.handle)

    
if __name__ == '__main__':
    pico = PicoScopeDAQ()
    pico.setup_channel()
    pico.setup_trigger(threshold=1.5)
    times, channelA, _ = pico.start(channel='A')
    pico.close_scope()


    plt.figure()
    plt.plot(times, channelA)
    plt.xlabel('time (s)')
    plt.ylabel('Voltage (V)')
    plt.show()


