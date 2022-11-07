from xml.etree.ElementTree import PI
from labequipment.picoscope_daq import PicoScopeDAQ
import matplotlib.pyplot as plt


pico = PicoScopeDAQ()
pico.setup_channel()
pico.start()
pico.close_scope()


plt.figure()
plt.plot(times, a)
plt.show()
