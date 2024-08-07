
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

def get_overview_buffers_a(buffers, _overflow, _triggered_at, _triggered, _auto_stop, n_values):
    adc_values_a.extend(buffers[0][0:n_values])

callback_a = CALLBACK(get_overview_buffers_a)




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
            raise Exception('No appropriate timebase was identifiable - you might be asking for too many samples')

    return current_timebase - 1, old_time_interval, time_units




class PicoScopeDAQ:
    """
    PicoScopeDAQ is a simple python interface to collect data from the picoscope 2000 series. 

    Unfortunately not all 2000 series use the same python sdk drivers. 
    We've written two versions of this code. One for the 2000 series and one for the 2000a series. The classes
    have the same name and interface but are in different files. Hence you should be able to change code by modifying the import statement.
    
    Picoscope 2204A uses this file
    Picoscope 2208B uses the other file.
    You can check other models by looking at datasheet linked to below.

    Installation: To run this code you need to download and install the drivers. 
    https://www.picotech.com/downloads. 
    You want 64bit PicoSDK. Once you've installed this then you can 
    pip install this code:
    "pip install git+https://github.com/MikeSmithLabTeam/labequipment"

    Useful additional info for programming is found
    here: https://www.picotech.com/download/manuals/ps2000pg.en-10.pdf

    'block' mode fills the buffer on the device and then stops returning the data.
    This can be used at the highest samplerate supported by the device. You can collect either a single
    or dual channel. Single channel uses the whole memory and dual channel splits memory between them.
    For full specs of each model of oscilloscope see here: https://www.picotech.com/download/datasheets/picoscope-2000-series-data-sheet-en.pdf

    'stream' mode continuously collects and transfers data to the 
    pc's buffer allowing long time data collection but at the expense of speed. The code is implemented
    only for use with channel A. I found there were issues trying to get both to run without losing data

    Import statement

        from labequipment.picoscope_2000 import PicoScopeDAQ
    
    Example Usage in Block Mode:

        pico = PicoScopeDAQ()
        pico.setup_channel()
        pico.setup_trigger(threshold=1.5)
        times, channelA, _ = pico.start()
        pico.close_scope()

    Example Usage in Stream Mode:

        pico = PicoScopeDAQ()
        pico.setup_channel(channel='A', samples=1000)
        pico.setup_trigger(threshold=1.5)
        times, channelA, _ = pico.start_streaming(collect_time=5)
        pico.close_scope()
    
    Example Usage with quick_setup:
        param_dict = {'channel':'B', 'samples':5000, 'trigger':None}
        pico=PicoScopeDAQ()
        pico.quick_setup(param_dict)
        times, _, channelB = pico.start()
 
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

    def quick_setup(self, param_dict,**kwargs):
        """
        quick setup expects a dictionary of key:value pairs corresponding to inputs from setup_channel and setup_trigger. You can supply some or
        none. If you don't want a trigger supply 'trigger':None as a key:value pair in your dictionary
        """
        self.setup_channel(**param_dict)
        if 'trigger' in param_dict.keys():
            if 'trigger' != None:
                self.setup_trigger(**param_dict)

    def setup_channel(self, channel='A', sample_rate=1000, coupling='DC', voltage_range=2, oversampling=1, **kwargs):
        """
        Channel can be 'A','B' or 'Both'
        samples - max depends on device and also on how many channels are used. 
        
                Model 2204a has 8kS - 1 channel = 8000 but 2 channels ~ 3965 samples,
        
        sample_rate - max depends on device. The actual sample rate is calculated and chosen to be the nearest available value more than the one you request. The value used is printed to the terminal. You can also access this by calling self.Device 
        range  - can be 0.02,0.05,0.1,0.2,0.5,1,2,5,10,20V 
        coupling  - can take values 'DC' or 'AC'
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
        else:
            self._v_range_a=ps2000.PS2000_VOLTAGE_RANGE['PS2000_' + str(voltage_range) + self.voltage_unit]
            self._v_range_b=ps2000.PS2000_VOLTAGE_RANGE['PS2000_' + str(voltage_range) + self.voltage_unit]

        self.sample_rate = sample_rate
        self.oversampling=oversampling
    
        if coupling == 'DC':
            coupling_id=1
        else:
            coupling_id=0
        
        channel_A=0
        channel_B=1

        if channel == 'A':     
            self.channel_a=True
            self.channel_b=False
            ps2000._python_set_channel(self.device.handle,channel_A, True,coupling_id,self._v_range_a,None)
            ps2000._python_set_channel(self.device.handle,channel_B, False,coupling_id,self._v_range_a,None)
        elif channel == 'B':
            self.channel_a=False
            self.channel_b=True
            ps2000._python_set_channel(self.device.handle,channel_A, False,coupling_id,self._v_range_b,None)
            ps2000._python_set_channel(self.device.handle,channel_B, True,coupling_id,self._v_range_b,None)
        elif channel == 'Both':
            self.channel_a=True
            self.channel_b=True
            ps2000._python_set_channel(self.device.handle,channel_A, True,coupling_id,self._v_range_a,None)
            ps2000._python_set_channel(self.device.handle,channel_B, True,coupling_id,self._v_range_b,None)
        else:
            raise ValueError('Channel must be A, B or Both')

        
    def setup_trigger(self,channel='A', enable=True, threshold=0, rising=True,  delay=0, max_wait=0, **kwargs):
        """
        This is optional and if not called the data will collect immediately.

        channel - specifies channel on which trigger acts
        threshold - value at which trigger is activated
        rising - True, falling=False
        delay - data startpoint in time relative to trigger. Defined as percentage of total samples. 0 means trigger is at the first data value in the block. -50 means it is in the middle of the block. Possible values are -100 to 100.
        max_wait - Value in s to wait for the trigger. 0 means wait forever

        This is optional and if not called the data will collect immediately.

        """

        if not enable:
            raise ValueError('enable trigger not implemented for this model')
    
        self._direction = 0 if rising else 1

        if channel=='A':
            self.trigger_channel = 0
        elif channel=='B':
            self.trigger_channel=1
        
        self._delay = delay
        self._max_wait = max_wait

        millivolts = threshold*1000
        self._converted_threshold = mV2adc(millivolts, self._v_range_a, c_int16(32767))       

        
    def start(self, samples=2000):
        """
        Collect data in block mode. 

        start will collect data from setup channels.
        block mode fills picoscope buffer once and then returns the data  (Fast, but limited time)

        Signal amplitude in V
        Time in s
        """

        self.samples = samples
        self.timebase, self.interval, self.time_units = get_timebase(self.device, samples, 1E9/self.sample_rate, oversample=self.oversampling)

        percent_delay = int(100*self._delay*self.sample_rate/self.samples)
        if percent_delay < -100 or percent_delay > 100:
            raise ValueError('Delay must not require value greater than number of samples collected. ie |delay| < samples/sample_rate')
        
        ps2000.ps2000_set_trigger(c_int16(self.device.handle), c_int16(self.trigger_channel), c_int16(self._converted_threshold), c_int16(int(self._direction)), c_int16(percent_delay), c_int16(int(self._max_wait*1000)))

        print("Using sample rate: {} Hz".format(1E9/self.interval))

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
            

        time_s=np.array(times[:])/1E9 # Convert from ns to s
        
        return time_s, channel_a_v, channel_b_v            
    

    def start_streaming(self, collect_time=5, aggregate=1):
        """
        Collect data in streaming mode

        Only channel A can be used in streaming mode.

        stream mode transfers data repeatedly as requested with no gaps.
        **Important** if you call start_streaming multiple times you will get 2 sets of data concatenated and all the timing will be wrong.

        collect_time: time in seconds to collect for in stream mode, has no effect on block mode
        aggregate: number of values averaged together and returned as single point in Stream mode
        """

        samples_in_buffer = 1000
        _, self.interval, _ = get_timebase(self.device, samples_in_buffer, 1E9/self.sample_rate, oversample=self.oversampling)

        ps2000.ps2000_run_streaming_ns(
                    c_int16(self.device.handle),
                    c_uint32(self.interval),
                    2,
                    c_uint32(samples_in_buffer),
                    c_int16(False),
                    c_uint32(aggregate),
                    c_uint32(100000)
                    )

        start_time = time_ns()
        data=[]
        while time_ns() - start_time < collect_time*1E9:               
            ps2000.ps2000_get_streaming_last_values(
                self.device.handle,
                callback_a
                )
            
        end_time = time_ns()
        ps2000.ps2000_stop(self.device.handle)
        data_a_V = np.array(adc2mV(adc_values_a, self._v_range_a, c_int16(32767)))/1000
        
        times = np.linspace(0, (end_time - start_time) * 1e-9, len(data_a_V))

        return times, data_a_V, np.zeros(np.shape(data_a_V))

    def close_scope(self):
        ps2000.ps2000_close_unit(self.device.handle)

