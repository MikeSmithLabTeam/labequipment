from labequipment.picoscope_2000a import PicoScopeDAQ
import matplotlib.pyplot as plt
import numpy as np
from picosdk.ps2000a import ps2000a as ps

if __name__ == '__main__':
    sample_rate = 1/(5e-9)
    print(sample_rate)
    
    sample_interval = 1/sample_rate
    print(sample_interval)
    if sample_interval*1e9 <= 4:
        timebase=0
        while (2**timebase < sample_interval*1e9):
            timebase+=1
        timebase = int(timebase)
    else:
        timebase = int(np.ceil(sample_interval*125000000+2))
        print('Timebase:', timebase)
    
    """
    pico = PicoScopeDAQ()
    pico.setup_channel(channel='A', samples=1000, sample_rate=5000, voltage_range=10)
    #pico.setup_channel(channel='B', samples=1000, sample_rate=5000)
    time, dataA, dataB= pico.start()
    

    pico.close_scope()    
   
    plt.figure()
    plt.plot(time, dataA)
    plt.show()
    
    """
