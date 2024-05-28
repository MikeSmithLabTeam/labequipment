
import sys
sys.path.insert(0, '../labequipment/')
import labequipment.picoscope as picoscope
import matplotlib.pyplot as plt


"""This is not a propert test.

1. Connect the picoscope to a signal generator with freuency 2hz and square wave.
2. run the code and check you get a response.

You need to test for both the 2204A and the 2208B as they use different drivers and code.
"""

def test_picoscope_blockmode():
    pico = picoscope.PicoScopeDAQ()
    pico.setup_channel(channel='A', sample_rate=500, voltage_range=10)
    pico.setup_trigger(channel='A', threshold=2.5, delay=3)
    time, dataA, dataB= pico.start(samples=2000)
    pico.close_scope()    

    plt.figure()
    plt.plot(time, dataA)
    plt.show()
    
def test_picoscope_streammode():
    pico = picoscope.PicoScopeDAQ()
    pico.setup_channel(channel='A', sample_rate=30000, voltage_range=10)
    pico.setup_trigger(channel='A', threshold=2.5, delay=3)
    time, dataA, dataB= pico.start_streaming(collect_time=3)
    pico.close_scope()    

    plt.figure()
    plt.plot(time, dataA)
    plt.show()


if __name__ == '__main__':
    test_picoscope_blockmode()
    test_picoscope_streammode()