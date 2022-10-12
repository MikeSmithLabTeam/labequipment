
from ctypes import byref, c_byte, POINTER, c_int16, c_int32, c_float, c_uint32, sizeof
from gc import collect
from time import sleep, time_ns

from picosdk.ps2000 import ps2000
from picosdk.functions import assert_pico2000_ok, adc2mV, mV2adc
from picosdk.PicoDeviceEnums import picoEnum
from picosdk.ctypes_wrapper import C_CALLBACK_FUNCTION_FACTORY

import matplotlib.pyplot as plt
import numpy as np

CALLBACK = C_CALLBACK_FUNCTION_FACTORY(None, POINTER(POINTER(c_int16)), c_int16, c_uint32, c_int16, c_int16, c_uint32)

adc_values_a = []
adc_values_b = []

def get_overview_buffers_a(buffers, _overflow, _triggered_at, _triggered, _auto_stop, n_values):
    adc_values_a.extend(buffers[0][0:n_values])

def get_overview_buffers_b(buffers, _overflow, _triggered_at, _triggered, _auto_stop, n_values):
    adc_values_b.extend(buffers[1][0:n_values])

callback_a = CALLBACK(get_overview_buffers_a)
callback_b = CALLBACK(get_overview_buffers_b)



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
    """
    PicoScopeDAQ is a simple python interface to collect data from the picoscope 2000 series. 

    Installation: To run this code you need to download and install the drivers. 
    https://www.picotech.com/downloads
    You want 64bit PicoSDK. Once you've installed this then you can 
    pip install this code:
    "pip install git+https://github.com/MikeSmithLabTeam/labequipment"

    'block' mode fills the buffer on the device and then stops returning the data.
    This can be used at the highest samplerate supported by the device. You can collect either a single
    or dual channel. Single channel uses the whole memory and dual channel splits memory between them.
    For full specs of each model of oscilloscope see here: https://www.picotech.com/download/datasheets/picoscope-2000-series-data-sheet-en.pdf

    'stream' mode continuously collects and transfers data to the 
    pc's buffer allowing long time data collection but at the expense of speed. Although the code is implemented
    for dual channel this seems to create issues so its recommended to only collect on a single channel at a time.

    Import statement

        from labequipment.picoscope_daq import PicoScopeDAQ
    
    Example Usage in Block Mode:

        pico = PicoScopeDAQ()
        pico.setup_channel()
        pico.setup_trigger(threshold=1.5)
        times, channelA, _ = pico.start(channel='A')
        pico.close_scope()

    Example Usage in Stream Mode:

        pico = PicoScopeDAQ()
        pico.setup_channel()
        pico.setup_trigger(threshold=1.5)
        times, channelA = pico.start(channel='A', mode='stream', collect_time=5)
        pico.close_scope()
 
    Plot the data:

        plt.figure()
        plt.plot(times, channelA)
        plt.xlabel('time (s)')
        plt.ylabel('Voltage (V)')
        plt.show()
    
    """


    def __init__(self):
        """This assumes only one device connected to system. Checks device found and instantiates object"""
        self.device = ps2000.open_unit()
        print('Device info: {}'.format(self.device.info))
        self.channel_a=False
        self.channel_b=False

    def setup_channel(self, channel='A', samples=3000, sample_rate=1000, coupling='DC', voltage_range=2, oversampling=1):
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

        if channel == 'A':
            self._v_range_a=ps2000.PS2000_VOLTAGE_RANGE['PS2000_' + str(voltage_range) + self.voltage_unit]
        elif channel == 'B':
            self._v_range_b=ps2000.PS2000_VOLTAGE_RANGE['PS2000_' + str(voltage_range) + self.voltage_unit]

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
            ps2000._python_set_channel(self.device.handle,channel_A, 1,coupling_id,self._v_range_a,None)
            self.channel_a=True
            if self.channel_b == False:
                #Turn off other channel if not already set to increase memory.
                ps2000._python_set_channel(self.device.handle,channel_B, 0,coupling_id,self._v_range_a,None) 
        elif channel == 'B':
            ps2000._python_set_channel(self.device.handle,channel_B, 1,coupling_id,self._v_range_b,None)
            self.channel_b=True
            if self.channel_a == False:
                ps2000._python_set_channel(self.device.handle,channel_A, 0,coupling_id,self._v_range_b,None) 
        self.timebase, self.interval, self.time_units = get_timebase(self.device, samples, 1E9/sample_rate, oversample=oversampling)
        

    def setup_trigger(self,channel='A', threshold=0, direction=0,  delay=0, wait=0):
        """
        This is optional and if not called the data will collect immediately.

        channel - specifies channel on which trigger acts
        threshold - value at which trigger is activated
        direction - 0=rising, 1=falling
        delay - data startpoint in time relative to trigger. Defined as percentage of total samples
        wait - Value in ms to wait for the trigger. 0 will wait indefinitely
        """

        if channel=='A':
            channel_id = 0
        elif channel=='B':
            channel_id=1

        #Convert threshold
        millivolts = threshold*1000
        if channel == 'A':
            converted_threshold = mV2adc(millivolts, self._v_range_a, c_int16(32767))
        elif channel == 'B':
            converted_threshold = mV2adc(millivolts, self._v_range_a, c_int16(32767))

        ps2000.ps2000_set_trigger(c_int16(self.device.handle), c_int16(channel_id), c_int16(converted_threshold), c_int16(direction), c_int16(delay), c_int16(wait))

    def start(self, mode='block', collect_time=5, aggregate=1):
        """
        start will collect data from setup channels.
        mode:   'block' fills picoscope buffer once and then returns the data  (Fast, but limited time)
                'stream' transfers data repeatedly as requested with no gaps    (Bit Slower, call Stop when you've had enough)
        collect_time: time in seconds to collect for in stream mode
        aggregate: number of values averaged together and returned as single point in Stream mode.
        """
        channel_a_v, channel_b_v = None, None

        collection_time = c_int32()

        if mode == 'Block':
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
            if self.channel_a:
                buffer_a = (c_int16 * self.samples)()
            if self.channel_b:
                buffer_b = (c_int16 * self.samples)()
         
            overflow = c_byte(0)

            assert self.channel_a or self.channel_b, 'You must setup a channel before running start'

            if self.channel_a and self.channel_b:
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
                channel_a_v = np.array(adc2mV(buffer_a, self._v_range_a, c_int16(32767)))/1000 # convert from mV to V
                channel_b_v = np.array(adc2mV(buffer_b, self._v_range_b, c_int16(32767)))/1000   
            elif self.channel_a:
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
                channel_a_v = np.array(adc2mV(buffer_a, self._v_range_a, c_int16(32767)))/1000 # convert from mV to V
            elif self.channel_b:
                res = ps2000.ps2000_get_times_and_values(
                    self.device.handle,
                    byref(times),
                    byref(buffer_b),
                    None,
                    None,
                    None,
                    byref(overflow),
                    self.time_units,  
                    self.samples,
                    )
                channel_b_v = np.array(adc2mV(buffer_b, self._v_range_b, c_int16(32767)))/1000 # convert from mV to V      

            times=np.array(times[:])/1E9 # Convert from ns to s
           
            return times, channel_a_v, channel_b_v

        
        elif mode == 'stream':
            ps2000.ps2000_run_streaming_ns(
                    c_int16(self.device.handle),
                    c_uint32(self.interval),
                    2,
                    c_uint32(self.samples),
                    c_int16(False),
                    c_uint32(aggregate),
                    c_uint32(15000)
                    )

            start_time = time_ns()
            data=[]
            while time_ns() - start_time < collect_time*1E9:               
                ps2000.ps2000_get_streaming_last_values(
                    self.device.handle,
                    callback_a
                    )
                #ps2000.ps2000_get_streaming_last_values(
                #    self.device.handle,
                #    callback_b
                #    )

            end_time = time_ns()
            ps2000.ps2000_stop(self.device.handle)
            data_a_V = np.array(adc2mV(adc_values_a, self._v_range_a, c_int16(32767)))/1000
            #data_b_V = np.array(adc2mV(adc_values_b, self._v_range_b, c_int16(32767)))/1000
            
            times = np.linspace(0, (end_time - start_time) * 1e-6, len(data_a_V))
            print(np.size(times))
            print(np.size(data_a_V))
            #print(np.size(data_b_V))
            return times, data_a_V#, data_b_V
    
    def close_scope(self):
        ps2000.ps2000_close_unit(self.device.handle)

