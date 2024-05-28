from ._picoscope_2000a import PicoScopeDAQ as PicoScopeDAQ2000a
from ._picoscope_2000 import PicoScopeDAQ as PicoScopeDAQ2000

def PicoScopeDAQ():
    """This function is pretending to be a class! It will return the correct class for the picoscope connected. The drivers for 2204A and 2208B are different and so is the sdk. The classes are designed with the same interface so will work the same irrespective of which unit you are using. See comments at top of _picoscope_2000.py if you are working with the 2204A and _picoscope_2000a.py if working with the 2208B."""
    try:
        pico = PicoScopeDAQ2000a()
    except:
        print("No 2000a found, trying 2000")
        try:
            pico = PicoScopeDAQ2000()
        except:
            print("No 2000 found either")
            pico = None
    return pico