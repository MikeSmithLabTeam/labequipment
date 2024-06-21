import time

class Stepper():
    """
    Class to manage the movement of stepper motors
    """
    def __init__(self, ard):
        """ Initialise with an instance of arduino.Arduino"""
        self.ard = ard

    def move_motor(self, motor_no, steps, direction, steps_per_sec=2000/128):
        """
        Generate the message to be sent to self.ard.send_serial_line

        Inputs:
        motor_no: 1 or 2
        steps: int
        direction: either '+' or '-'
        max steps 100000 --> Though it may bottom out etc before that!
        """
        self.motor_timeout = 10 + (1/steps_per_sec) * abs(steps)
        message = 'M' + str(motor_no) + direction + str(steps) + '\n'
        self.ard.send_serial_line(message)
        time.sleep(0.1)
        success = self.get_motor_confirmation()
        return success

    def get_motor_confirmation(self):
        """The Arduino Sketch for stepper motors 'Shaker_Motor_v2.ino' is set up
        so that when a message is sent to it to move the motor is replies

        \n M1+3000\n

        After the motor has moved it then sends a confirmation it is finished:

        M1 moved\n    
        
        This function will return success=True if it received confirmation that the motor has moved.        
        """
         
        # Wait for bytes in the serial buffer until the timeout
        tic = time.time()
        while True:
            toc = time.time()
            if self.ard.port.inWaiting() > 0:
                reply = self.ard.read_serial_line()  # Read the bytes
                if 'moved' in reply:
                    return True
            if toc - tic > self.motor_timeout:
                return False
            time.sleep(0.1)
        

