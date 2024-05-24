from calendar import c
import time

from picosdk.ps2000a import ps2000a as ps
from picosdk.functions import assert_pico_ok, adc2mV, mV2adc
import ctypes

import matplotlib.pyplot as plt
import numpy as np



def get_timebase(device, samples, sample_rate, oversample=1):
    """sample_rate is in Hz but timebase is in ns."""
    sample_interval = 1/sample_rate
    
    if sample_interval*1e9 <= 4:
        timebase=0
        while (2**timebase < sample_interval*1e9):
            timebase+=1
        timebase = int(timebase)
    else:
        timebase = int(np.ceil(sample_interval*125000000+2))
        print('Timebase:', timebase)

    timeIntervalns = ctypes.c_float()
    returnedMaxSamples = ctypes.c_int32()
    oversample = ctypes.c_int16(0)

    status["getTimebase2"] = ps.ps2000aGetTimebase2(device,
                        timebase,
                        samples,
                        ctypes.byref(timeIntervalns),
                        oversample,
                        ctypes.byref(returnedMaxSamples),
                        0)
    assert_pico_ok(status["getTimebase2"])
    
    return current_timebase - 1, old_time_interval, time_units




class PicoScopeDAQ:
    """
    PicoScopeDAQ is a simple python interface to collect data from the picoscope 2000a series. 

    Unfortunately not all 2000 series use the same python sdk drivers. 
    We've written two versions of this code. One for the 2000 series and one for the 2000a series. The classes
    have the same name but are in different files. Hence you should be able to change code by modifying the import statement.
    
    Picoscope 2208B uses this file
    Picoscope 2204A uses the other file.
    You can check other models by looking at datasheet linked to below.

    Installation: To run this code you need to download and install the drivers. 
    https://www.picotech.com/downloads. 
    You want 64bit PicoSDK. Once you've installed this then you can 
    pip install this code:
    "pip install git+https://github.com/MikeSmithLabTeam/labequipment"

    Useful additional info for programming is found
    here: https://www.picotech.com/download/manuals/picoscope-2000-series-a-api-programmers-guide.pdf

    'block' mode fills the buffer on the device and then stops returning the data.
    This can be used at the highest samplerate supported by the device. You can collect either a single
    or dual channel. Single channel uses the whole memory and dual channel splits memory between them.
    For full specs of each model of oscilloscope see here: https://www.picotech.com/download/datasheets/picoscope-2000-series-data-sheet-en.pdf

    'stream' mode continuously collects and transfers data to the 
    pc's buffer allowing long time data collection but at the expense of speed. The code is implemented
    only for use with channel A. I found there were issues trying to get both to run without losing data

    Import statement

        from labequipment.picoscope_daq import PicoScopeDAQ
    
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
        times, channelA, _ = pico.start(mode='stream', collect_time=5)
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
        self.status = {}
        self._chandle = ctypes.c_int16()
        
        self.status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(self._chandle), None)
        #assert(self.status["openunit"]==0, "No Picoscope found, check the model matches the code you are using. Read the docs above!")
        
        self.channel_a=False
        self.channel_b=False

    def quick_setup(self, param_dict,**kwargs):
        """
        quick setup expects a dictionary of key:value pairs corresponding to inputs from setup_channel and setup_trigger. You can supply some or
        none. If you don't want a trigger supply 'trigger':None as a key:value pair in your dictionary
        """
        pass

    def setup_channel(self, channel='A', samples=3000, sample_rate=1000, coupling='DC', voltage_range=2, oversampling=1, **kwargs):
        """
        Channel can be 'A', 'B' or 'Both'
        samples - max depends on device and also on how many channels are used. 
        
                Model 2204a has 8kS - 1 channel = 8000 but 2 channels ~ 3965 samples,
        
        sample_rate - max depends on device. The actual sample rate is calculated and chosen to be the nearest available value more than the one you request. The value used is printed to the terminal. You can also access this by calling self.Device 
        voltage_range  - can be 0.02,0.05,0.1,0.2,0.5,1,2,5,10,20V 
        coupling  - can take values 'DC' or 'AC'
        """
        
        if voltage_range in [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            self._v_range = voltage_range
        else:
            raise ValueError("Voltage range must be 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10 or 20")
        
        _coupling = ps.PS2000A_COUPLING['PS2000A_AC'] if coupling=='AC' else ps.PS2000A_COUPLING['PS2000A_DC']
    
        self.samples=samples
        self.sample_rate=sample_rate
        
        channel_A = 0
        channel_B = 1
        enabled=True
        not_enabled=False

        if channel=='A':
            # Set up channel A
            self.status["setChA"] = ps.ps2000aSetChannel(self._chandle, channel_A, enabled, _coupling, self._v_range, 0)
            self.status["setChB"] = ps.ps2000aSetChannel(self._chandle, channel_B, not_enabled, _coupling, self._v_range, 0)
            #assert_pico_ok(self.status["setChA"])
        # Set up channel B
        elif channel=='B' or channel=='Both':
            self.status["setChA"] = ps.ps2000aSetChannel(self._chandle, channel_A, not_enabled, _coupling, self._v_range, 0)
            self.status["setChB"] = ps.ps2000aSetChannel(self._chandle, channel_B, enabled, _coupling, self._v_range, 0)
            #assert_pico_ok(self.status["setChB"])
        elif channel=='Both':
            print('Test')
            self.status["setChA"] = ps.ps2000aSetChannel(self._chandle, channel_A, enabled, _coupling, self._v_range, 0)
            self.status["setChB"] = ps.ps2000aSetChannel(self._chandle, channel_B, enabled, _coupling, self._v_range, 0)
            #assert_pico_ok(self.status["setChA"])
            #assert_pico_ok(self.status["setChB"])
        else:
            raise ValueError("Channel must be 'A', 'B' or 'Both'")
        
   
    def setup_trigger(self, channel='A', threshold=0, pre_trigger_samples=0, direction=0, max_wait=0, enable=True, **kwargs):
        """
        This is optional and if not called the data will collect immediately.

        channel - specifies channel on which trigger acts
        threshold - value at which trigger is activated
        pre_trigger_samples - number of samples before trigger event.
        direction - 2=rising, 1=falling
        delay - delay in seconds from trigger to start of data collection
        enable - enable (true) or disable (False) trigger
        max_wait - time in ms to wait for trigger before giving up. 0 means wait forever
        """
        
        self._preTriggerSamples = pre_trigger_samples
        

        converted_threshold = mV2adc(millivolts, self._v_range, c_int16(32767))
        self.status["trigger"] = ps.ps2000aSetSimpleTrigger(self._chandle, 1, 0, converted_threshold, 2, 0, max_wait)
        assert_pico_ok(self.status["trigger"])

    def start(self):
        """
        Collect data in block mode. 

        start will collect data from setup channels.
        block mode fills picoscope buffer once and then returns the data  (Fast, but limited time)
        """
        if not hasattr(self, '_preTriggerSamples'):
            self._preTriggerSamples = 0

        # Get timebase information
        # WARNING: When using this example it may not be possible to access all Timebases as all channels are enabled by default when opening the scope.  
        # To access these Timebases, set any unused analogue channels to off.
        # handle = chandle
        # timebase = 8 = timebase
        # noSamples = totalSamples
        # pointer to timeIntervalNanoseconds = ctypes.byref(timeIntervalNs)
        # pointer to totalSamples = ctypes.byref(returnedMaxSamples)
        # segment index = 0
        
        get_timebase(self._chandle, self.samples, sample_rate)
        
        print(self.status["getTimebase2"])
        assert_pico_ok(self.status["getTimebase2"])
        # Run block capture
        # handle = chandle
        # number of pre-trigger samples = preTriggerSamples
        # number of post-trigger samples = PostTriggerSamples
        # timebase = 8 = 80 ns = timebase (see Programmer's guide for mre information on timebases)
        # oversample = 0 = oversample
        # time indisposed ms = None (not needed in the example)
        # segment index = 0
        # lpReady = None (using ps2000aIsReady rather than ps2000aBlockReady)
        # pParameter = None
        self.status["runBlock"] = ps.ps2000aRunBlock(self._chandle,
                                                self._preTriggerSamples,
                                                self.samples - self._preTriggerSamples,
                                                timebase,
                                                oversample,
                                                None,
                                                0,
                                                None,
                                                None)
        assert_pico_ok(self.status["runBlock"])
        # Check for data collection to finish using ps2000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps2000aIsReady(self._chandle, ctypes.byref(ready))

        # Create buffers ready for assigning pointers for data collection
        bufferAMax = (ctypes.c_int16 * self.samples)()
        bufferAMin = (ctypes.c_int16 * self.samples)() # used for downsampling which isn't in the scope of this example
        bufferBMax = (ctypes.c_int16 * self.samples)()
        bufferBMin = (ctypes.c_int16 * self.samples)() # used for downsampling which isn't in the scope of this example

        # Set data buffer location for data collection from channel A
        # handle = chandle
        # source = PS2000A_CHANNEL_A = 0
        # pointer to buffer max = ctypes.byref(bufferDPort0Max)
        # pointer to buffer min = ctypes.byref(bufferDPort0Min)
        # buffer length = self.samples
        # segment index = 0
        # ratio mode = PS2000A_RATIO_MODE_NONE = 0
        self.status["setDataBuffersA"] = ps.ps2000aSetDataBuffers(self._chandle,
                                                            0,
                                                            ctypes.byref(bufferAMax),
                                                            ctypes.byref(bufferAMin),
                                                            self.samples,
                                                            0,
                                                            0)

        assert_pico_ok(self.status["setDataBuffersA"])

        # Set data buffer location for data collection from channel B
        # handle = chandle
        # source = PS2000A_CHANNEL_B = 1
        # pointer to buffer max = ctypes.byref(bufferBMax)
        # pointer to buffer min = ctypes.byref(bufferBMin)
        # buffer length = totalSamples
        # segment index = 0
        # ratio mode = PS2000A_RATIO_MODE_NONE = 0
        self.status["setDataBuffersB"] = ps.ps2000aSetDataBuffers(self._chandle,
                                                            1,
                                                            ctypes.byref(bufferBMax),
                                                            ctypes.byref(bufferBMin),
                                                            self.samples,
                                                            0,
                                                            0)
        assert_pico_ok(self.status["setDataBuffersB"])

        # Create overflow location
        overflow = ctypes.c_int16()
        # create converted type totalSamples
        cTotalSamples = ctypes.c_int32(self.samples)

        # Retried data from scope to buffers assigned above
        # handle = chandle
        # start index = 0
        # pointer to number of samples = ctypes.byref(cTotalSamples)
        # downsample ratio = 0
        # downsample ratio mode = PS2000A_RATIO_MODE_NONE
        # pointer to overflow = ctypes.byref(overflow))
        self.status["getValues"] = ps.ps2000aGetValues(self._chandle, 0, ctypes.byref(cTotalSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])


        # find maximum ADC count value
        # handle = chandle
        # pointer to value = ctypes.byref(maxADC)
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps2000aMaximumValue(self._chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # convert ADC counts data to mV
        adc2mVChAMax =  adc2mV(bufferAMax, self._v_range, maxADC)
        adc2mVChBMax =  adc2mV(bufferBMax, self._v_range, maxADC)

        # Create time data
        time = np.linspace(0, ((cTotalSamples.value)-1) * timeIntervalns.value, cTotalSamples.value)
        return time, adc2mVChAMax, adc2mVChBMax
            

    def start_streaming(self, collect_time=5, aggregate=1):
        """
        Collect data in streaming mode

        stream mode transfers data repeatedly as requested with no gaps.
        **Important** if you call start_streaming multiple times you will get 2 sets of data concatenated and all the timing will be wrong.

        collect_time: time in seconds to collect for in stream mode, has no effect on block mode
        aggregate: number of values averaged together and returned as single point in Stream mode
        """
        pass

    def _stop(self):
        # Stop the scope
        # handle = chandle
        self.status["stop"] = ps.ps2000aStop(self._chandle)
        assert_pico_ok(self.status["stop"])      

    def close_scope(self):
        self.status["close"] = ps.ps2000aCloseUnit(self._chandle)
        assert_pico_ok(self.status["close"])

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close_scope()
        return True
