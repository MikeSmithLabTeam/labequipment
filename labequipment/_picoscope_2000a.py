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

    timeIntervalns = ctypes.c_float()
    returnedMaxSamples = ctypes.c_int32()
    oversample = ctypes.c_int16(0)
  
    status =   {}

    status['getTimebase2']= ps.ps2000aGetTimebase2(device,
                        timebase,
                        samples,
                        ctypes.byref(timeIntervalns),
                        oversample,
                        ctypes.byref(returnedMaxSamples),
                        0)
    assert_pico_ok(status["getTimebase2"])

    return timebase, timeIntervalns, returnedMaxSamples, oversample




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

    'block' mode fills the buffer on the device and then stops, returning the data.
    This can be used at the highest samplerate supported by the device. You can collect either a single
    or dual channel. Single channel uses the whole memory and dual channel splits memory between them.
    For full specs of each model of oscilloscope see here: https://www.picotech.com/download/datasheets/picoscope-2000-series-data-sheet-en.pdf

    'stream' mode continuously collects and transfers data to the 
    pc's buffer allowing long time data collection but at the expense of speed (though not that much). The code is implemented only for use with channel A. I found there were issues trying to get both to run without losing data

    Import statement

        from labequipment.picoscope_2000a import PicoScopeDAQ
    
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
    
        if self.status["openunit"]!=0:
            raise ValueError("No Picoscope found, check the model matches the code you are using. Read the docs above!")
        
        self.channel_a=False
        self.channel_b=False

    def quick_setup(self, param_dict,**kwargs):
        """
        quick setup expects a dictionary of key:value pairs corresponding to inputs from setup_channel and setup_trigger. You can supply some or
        none. If you don't want a trigger supply 'trigger':None as a key:value pair in your dictionary
        """
        pass

    def setup_channel(self, channel='A', sample_rate=1000, coupling='DC', voltage_range=2, oversampling=1, **kwargs):
        """
        Channel can be 'A', 'B' or 'Both'        
        sample_rate - max depends on device. The actual sample rate is calculated and chosen to be the nearest available value more than the one you request. The value used is printed to the terminal. You can also access this by calling self.Device 
        voltage_range  - can be 0.02,0.05,0.1,0.2,0.5,1,2,5,10,20V 
        coupling  - can take values 'DC' or 'AC'
        """
        voltage_ranges = [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]
        if voltage_range in voltage_ranges:
            self._v_range = voltage_range
            #mv2adc in setup_trigger requires the number in the list above for the voltage range. The full list starts at 0.01 but this isn't supported by my card so +1.
            self._v_range_n = voltage_ranges.index(voltage_range)+1
        else:
            raise ValueError("Voltage range must be 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10 or 20")
        
        _coupling = ps.PS2000A_COUPLING['PS2000A_AC'] if coupling=='AC' else ps.PS2000A_COUPLING['PS2000A_DC']
    
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
            self.status["setChA"] = ps.ps2000aSetChannel(self._chandle, channel_A, enabled, _coupling, self._v_range, 0)
            self.status["setChB"] = ps.ps2000aSetChannel(self._chandle, channel_B, enabled, _coupling, self._v_range, 0)
            #assert_pico_ok(self.status["setChA"])
            #assert_pico_ok(self.status["setChB"])
        else:
            raise ValueError("Channel must be 'A', 'B' or 'Both'")        
   
    def setup_trigger(self, channel='A', enable=True, threshold=0, rising=True, delay=0, max_wait=30,  **kwargs):
        """
        This is optional and if not called the data will collect immediately.

        channel - specifies channel on which trigger acts
        enable - enable (true) or disable (False) trigger
        threshold - value (V) at which trigger is activated
        rising - True of falling false
        delay - delay in seconds from trigger to start of data collection
        max_wait - time in s to wait for trigger before giving up. 0 means wait forever
        """
        direction = 2 if rising else 1
        channel = 0 if 'A' else 1

        maxADC = ctypes.c_int16()
        ps.ps2000aMaximumValue(self._chandle, ctypes.byref(maxADC))      
        
        converted_threshold = mV2adc(0.5*threshold*1000, self._v_range_n, maxADC)
        self.status["trigger"] = ps.ps2000aSetSimpleTrigger(self._chandle, enable, channel, converted_threshold, direction, delay, max_wait*1000)
        assert_pico_ok(self.status["trigger"])

    def start(self, samples=3000):
        """
        Collect data in block mode. 

        start will collect data from setup channels.
        block mode fills picoscope buffer once and then returns the data  (Fast, but limited time)
        
        kwargs:
        samples - max depends on device and also on how many channels are used. Only used in block mode.
        
                Model 2204a has 8kS - 1 channel = 8000 but 2 channels ~ 3965 samples,
        
        returns
        Signal amplitude in V for both channels
        Time in s
        """        
        self.samples=samples

        # Get timebase information        
        timebase, timeIntervalns, maxSamples, oversample = get_timebase(self._chandle, self.samples, self.sample_rate)
        
        # Run block capture
        self.status["runBlock"] = ps.ps2000aRunBlock(self._chandle,
                                                0,
                                                self.samples,
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
        self.status["setDataBuffersA"] = ps.ps2000aSetDataBuffers(self._chandle,
                                                            0,
                                                            ctypes.byref(bufferAMax),
                                                            ctypes.byref(bufferAMin),
                                                            self.samples,
                                                            0,
                                                            0)

        assert_pico_ok(self.status["setDataBuffersA"])

        # Set data buffer location for data collection from channel B
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

        self.status["getValues"] = ps.ps2000aGetValues(self._chandle, 0, ctypes.byref(cTotalSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])


        # find maximum ADC count value
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps2000aMaximumValue(self._chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # convert ADC counts data to V
        chA_v =  np.array(adc2mV(bufferAMax, self._v_range, maxADC))/1000
        chB_v =  np.array(adc2mV(bufferBMax, self._v_range, maxADC))/1000

        # Create time data
        time_s = np.linspace(0, ((cTotalSamples.value)-1) * timeIntervalns.value/1e9, cTotalSamples.value)
        
        return time_s, chA_v, chB_v
            

    def start_streaming(self, collect_time=5):
        """
        Collect data in streaming mode

        stream mode transfers data repeatedly as requested with no gaps.
        **Important** if you call start_streaming multiple times you will get 2 sets of data concatenated and all the timing will be wrong.

        collect_time: time in seconds to collect for in stream mode, has no effect on block mode
        aggregate: number of values averaged together and returned as single point in Stream mode
        """
 
        enabled = 1
        disabled = 0
        analogue_offset = 0.0

        # Set up channel A
        channel_range = ps.PS2000A_RANGE['PS2000A_2V']
        self.status["setChA"] = ps.ps2000aSetChannel(self._chandle,
                                                ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
                                                enabled,
                                                ps.PS2000A_COUPLING['PS2000A_DC'],
                                                channel_range,
                                                analogue_offset)
        assert_pico_ok(self.status["setChA"])

        self.samples = int(collect_time * self.sample_rate)

        sizeOfOneBuffer = self.sample_rate #ie 1s of data regardless of sample rate
        if self.samples < sizeOfOneBuffer:
            numBuffersToCapture = 1
            self.samples = int(sizeOfOneBuffer)
        else:
            numBuffersToCapture = np.ceil(self.samples / sizeOfOneBuffer)
            self.samples = int(numBuffersToCapture * sizeOfOneBuffer)

        # Create buffers ready for assigning pointers for data collection
        bufferAMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)

        memory_segment = 0

        # Set data buffer location for data collection from channel A
        self.status["setDataBuffersA"] = ps.ps2000aSetDataBuffers(self._chandle,
                                                            ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
                                                            bufferAMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                            None,
                                                            sizeOfOneBuffer,
                                                            memory_segment,
                                                            ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'])
        assert_pico_ok(self.status["setDataBuffersA"])

        # Begin streaming mode:
        sampleInterval = ctypes.c_int32(int(1e6/self.sample_rate))
        sampleUnits = ps.PS2000A_TIME_UNITS['PS2000A_US']
        # We are not triggering:
        maxPreTriggerSamples = 0
        autoStopOn = 1
        # No downsampling:
        downsampleRatio = 1
        self.status["runStreaming"] = ps.ps2000aRunStreaming(self._chandle,
                                                        ctypes.byref(sampleInterval),
                                                        sampleUnits,
                                                        maxPreTriggerSamples,
                                                        self.samples,
                                                        autoStopOn,
                                                        downsampleRatio,
                                                        ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
                                                        sizeOfOneBuffer)
        assert_pico_ok(self.status["runStreaming"])

        actualSampleInterval = sampleInterval.value
        actualSampleIntervalNs = actualSampleInterval * 1000

        # We need a big buffer, not registered with the driver, to keep our complete capture in.
        bufferCompleteA = np.zeros(shape=self.samples, dtype=np.int16)
        global nextSample
        nextSample = 0
        autoStopOuter = False
        wasCalledBack = False


        def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
            global nextSample, autoStopOuter, wasCalledBack
            wasCalledBack = True
            destEnd = nextSample + noOfSamples
            sourceEnd = startIndex + noOfSamples
            bufferCompleteA[nextSample:destEnd] = bufferAMax[startIndex:sourceEnd]
            nextSample += noOfSamples
            if autoStop:
                autoStopOuter = True


        # Convert the python function into a C function pointer.
        cFuncPtr = ps.StreamingReadyType(streaming_callback)

        # Fetch data from the driver in a loop, copying it out of the registered buffers and into our complete one.
        while nextSample < self.samples and not autoStopOuter:
            wasCalledBack = False
            self.status["getStreamingLastestValues"] = ps.ps2000aGetStreamingLatestValues(self._chandle, cFuncPtr, None)
            if not wasCalledBack:
                # If we weren't called back by the driver, this means no data is ready. Sleep for a short while before trying
                # again.
                time.sleep(0.01)

        print("Done grabbing values.")

        # Find maximum ADC count value
        # handle = chandle
        # pointer to value = ctypes.byref(maxADC)
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps2000aMaximumValue(self._chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # Convert ADC counts data to mV
        chA_v = adc2mV(bufferCompleteA, channel_range, maxADC)

        # Create time data
        time_s = np.linspace(0, (self.samples-1) * actualSampleIntervalNs/1e9, self.samples)

        # Stop the scope
        # handle = chandle
        self.status["stop"] = ps.ps2000aStop(self._chandle)
        assert_pico_ok(self.status["stop"])

        return time_s, chA_v, np.zeros(np.shape(chA_v))

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
