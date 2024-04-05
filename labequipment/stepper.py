import time

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
        max steps 100000 --> Though it may bottom out etc before that!
        """
        self.motor_timeout = 1+ 0.065 * abs(steps)

        message = 'M' + str(motor_no) + direction + str(steps) + '\n'
        self.ard.send_serial_line(message)
        time.sleep(0.2)
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
        

        _ = self.ard.read_serial_line() #Throw away initial new line char
        _ = self.ard.read_serial_line() #Arduino reflects instruction

        # Wait for bytes in the serial buffer until the timeout
        tic = time.time()
        while (self.ard.port.inWaiting() == 0):  
            toc = time.time()
            if toc - tic > self.motor_timeout:
                break
            time.sleep(0.1)
        second_reply = self.ard.read_serial_line()  # Read the bytes
        if 'moved' in second_reply:
            return True
        else:
            return False
        

