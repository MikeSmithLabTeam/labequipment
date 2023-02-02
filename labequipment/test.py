import labvision.images as imgs
import numpy as np

im = np.ones((500,500,3))
print(np.shape(im))
res = imgs.crop_rectangle(im)
#im=imgs.draw_polygon(im, res.points)
#crop = res.bbox
#points = res.points
#mask = res.mask
#centre = np.mean(points, axis=0)
#im=imgs.draw_circle(im, 100,100,30)
#imgs.display(im)




"""from xml.etree.ElementTree import PI
from labequipment.picoscope_daq import PicoScopeDAQ
import matplotlib.pyplot as plt


pico = PicoScopeDAQ()
pico.setup_channel()
pico.start()
pico.close_scope()


plt.figure()
plt.plot(times, a)
plt.show()
"""