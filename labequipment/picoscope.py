from picoscope import ps2000
import numpy as np
import time

class Picoscope:

    def __init__(self):
        self.scope = ps2000.PS2000()
        waveform_desired_duration = 200E-3
        obs_duration = 3 * waveform_desired_duration
        sampling_interval = obs_duration / 4096
        (self.actualSamplingInterval, self.nSamples, maxSamples) = \
            self.scope.setSamplingInterval(sampling_interval, obs_duration)
        print('actual sampling interval = ', self.actualSamplingInterval)
        print('nsamples = ', self.nSamples)
        self.scope.setChannel('A', 'AC', 2.0, 0.0, enabled=True,
                           BWLimited=False)
        self.scope.setSimpleTrigger('A', 0, 'Falling', timeout_ms=100,
                                 enabled=True)
        self.scope.setChannel('B', 'AC', 2.0, 0.0, enabled=True, BWLimited=False)
        self.scope.setSimpleTrigger('B', 0, 'Falling', timeout_ms=100,
                                 enabled=True)

    def get_V(self, refine_range=False, channel='A'):
        s = time.time()
        if refine_range:
            channelRange = self.scope.setChannel(channel, 'AC', 2.0, 0.0,
                                              enabled=True, BWLimited=False)
            self.scope.runBlock()
            self.scope.waitReady()
            data = self.scope.getDataV(channel, self.nSamples,
                                    returnOverflow=False)
            vrange = np.max(data) * 1.5
            channelRange = self.scope.setChannel(channel, 'AC', vrange, 0.0,
                                              enabled=True, BWLimited=False)
        self.scope.runBlock()
        self.scope.waitReady()
        data = self.scope.getDataV(channel, self.nSamples, returnOverflow=False)
        times = np.arange(self.nSamples) * self.actualSamplingInterval
        return times, data, time.time() - s
