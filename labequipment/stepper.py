import time
import serial
from . import arduino

class Stepper():
    """
    Class to manage the movement of stepper motors
    """
    def __init__(self, ard):
        """ Initialise with an instance of arduino.Arduino"""
        self.ard = ard

    def move_motor(self, motor_no, steps, direction):
        """
        Generate the message to be sent to self.ard.send_serial_line

        Inputs:
        motor_no: 1 or 2
        steps: int
        direction: either '+' or '-'
        """
        message = 'M' + str(motor_no) + direction + str(steps) + '\n'
        self.ard.send_serial_line(message)

stepper = Stepper(stepper_arduino)
stepper.move_motor(1, 2000, "-")
