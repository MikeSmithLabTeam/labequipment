"""If you want to upload the operating system code for a RP2040-LCD accelerometer the files are
on mikesmithlab github page under the accelerometer repo"""

from labequipment.arduino import Arduino


def pk_acceleration(ard):
    """
    This function reads data from RPi Pico accelerometer and outputs current
    peak z-acceleration reading.

    ----Input: ----
    Object: Reads data from RPi Pico

    ----Returns: ----
    peak_z [float] : Peak accleration measured. (Γ)
    
    """
    ard.flush()
    line = ard.read_serial_line()
    data_vals=line.split(',')
    peak_z = float(data_vals[-1])
    return peak_z

def data_peak_z(ard, num_pts):
    """
    This function generates an array of peak z-acceleration values read over
    a chosen timescale. Calls function "pk_acceleration(object)" for peak 
    z-acceleration values.

    ----Input: ----
   num_pts [int] : number of values to collect.

    ----Returns: ----
    data_peak_z [numpy array] : array of peak z-acceleration values

    Example:
       with Arduino(settings) as ard:
           data_peak_z(ard, )
    """
    data_peak_z = []
    for i in range(num_pts):
        peak_z = pk_acceleration(ard)
        data_peak_z.append(peak_z)
    
    return data_peak_z