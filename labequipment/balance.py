import datetime
import time
import os

import numpy as np
#import cv2
from scipy import spatial

from labvision import camera, images
import arduino, stepper, shaker


STEPPER_CONTROL = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_5573532393535190E022-if00"

class Balancer:

    def __init__(self, camera, shape='polygon'):# shaker, camera, motors, centre_pt_fn, shape='hexagon'):
        """Balancer class handles levelling a shaker. 
        
        shaker an instance of Shaker() which controls vibration of shaker
        camera an instance of Camera() which allows pictures of experiment to be taken
        motors an instance of motors - usually Stepper()
        
        The basic principle is find the centre of the experiment by manually selecting the boundary.
        Type of boundary is defined by shape. The balancer then compares the centre as defined manually 
        and the centre as calculated on an image using centre_pt_fn. It then adjusts motors iteratively
        to move the measured and actual centre closer together.
        
        """
        #self.shaker = shaker
        #self.motors=motors      
        self.cam = camera
        self.boundary_shape=shape
        #self.centre_fn = centre_pt_fn
        self.find_boundary()

    def find_boundary(self):
        """Manually find the the experimental boundary
        This sets the target value of the centre.
        
        im is a grayscale image
        shape can be 'polygon', 'rectangle', 'circle'        
        """
        im = self.cam.get_frame()
        self.im_shape = im.shape


        if self.boundary_shape == 'polygon':
            res = images.crop_polygon(im)
            im=images.draw_polygon(im, res.points)
            crop = res.bbox
            points = res.points
            mask = res.mask
            centre = np.mean(points, axis=0)
        elif self.boundary_shape == 'rect':
            res = images.crop_rectangle(im)
            im=images.draw_polygon(im, res.points)
            crop = res.bbox
            points = res.points
            mask = res.mask
            centre = np.mean(points, axis=0)
        elif self.boundary_shape == 'circle':
            res = images.crop_circle(im)
            im=images.draw_circle(im, res.circle.xc, res.circle.yc, res.circle.r)
            crop = res.bbox
            points = res.points
            mask = res.mask
            centre = np.array([res.circle.xc, res.circle.yc])
        else:
            print('boundary shape not recognised: options are polygon, rect, circle')
            raise Exception
          
        im = images.crop_and_mask(im, crop, mask)
        #Draw central point based on boundary
        im = images.draw_circle(im, centre[0], centre[1], 3)
        images.display(im)

        return points, centre, crop, mask      

    def balance(self, repeats=5, threshold=10):
        balanced = False
        window = images.Displayer('Levelling')
        centre = (0, 0)
        while balanced is False:
            centres = []
            self.shaker.ramp(630, 500, 0.5)
            for f in range(repeats):
                self.f = f
                time.sleep(0.1)
                im = self.get_frame()
                centre = self.get_centre(im)
                centres.append(centre)
            mean_centre = np.mean(centres, axis=0)
            instruction, distance = self.find_instruction(mean_centre)
            annotated_im = self.annotate_image(im, centre, mean_centre,
                                               distance, centres)
            window.update_im(annotated_im)
            if distance > threshold:
                self.run_instruction(instruction)
                time.sleep(10)
            else:
                balanced = True
                print('BALANCED')
                print(datetime.datetime.now())
                self.shaker.change_duty(0)

    def run_instruction(self, instruction):
        val = self.step_size
        if instruction == 'Lower Motors 1 and 2':
            self.move_motor(1, val, '-')
            self.move_motor(2, val, '-')
        elif instruction == 'Lower Motor 1':
            self.move_motor(1, val, '-')
        elif instruction == 'Raise Motor 2':
            self.move_motor(2, val, '+')
        elif instruction == 'Raise Motors 1 and 2':
            self.move_motor(1, val, '+')
            self.move_motor(2, val, '+')
        elif instruction == 'Raise Motor 1':
            self.move_motor(1, val, '+')
        elif instruction == 'Lower Motor 2':
            self.move_motor(2, val, '-')

    def move_motor(self, motor, steps, direction):
        self.motors.move_motor(motor, steps, direction)

    def annotate_image(self, im, current_centre, mean_centre, distance,
                       centres):
        im = im.copy()
        if images.depth(im) != 3:
            im = images.gray_to_bgr(im)
        for centre in centres:
            im = images.draw_circle(im, centre[0], centre[1], 5,
                                    images.YELLOW)
        for circle in self.circles:
            im = images.draw_circle(im, circle[0], circle[1], circle[2], images.PINK)
        im = images.draw_circle(im, current_centre[0], current_centre[1], 5,
                                color=images.ORANGE, thickness=-1)
        im = images.draw_circle(im, self.centre[0], self.centre[1], 5,
                                images.RED)
        im = images.draw_circle(im, mean_centre[0], mean_centre[1], 5,
                                images.BLUE)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray centre', (10, 30), font, .5, images.RED, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Current centre', (10, 60), font, .5,
                         images.ORANGE, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Mean centre', (10, 90), font, .5, images.BLUE, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Pixel distance : {:.3f}'.format(
            distance), (10, 120), font, .5, images.GREEN, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Repeat: {}'.format(self.f), (10, 150), font, .5,
                         images.GREEN, 2, cv2.LINE_AA)

        im = cv2.putText(im, 'Old centres', (10, 180), font, .5, images.YELLOW,
                         2, cv2.LINE_AA)
        return im

    def find_instruction(self, centre):
        distance = ((centre[0] - self.centre[0]) ** 2 + (centre[1] - self.centre[1]) ** 2) ** 0.5

        corner_dists = spatial.distance.cdist(
            np.array(centre).reshape(1, 2), self.hex)
        closest_corner = np.argmin(corner_dists)
        instructions = {0: 'Raise Motor 2',
                        1: 'Raise Motors 1 and 2',
                        2: 'Raise Motor 1',
                        3: 'Lower Motor 2',
                        4: 'Lower Motors 1 and 2',
                        5: 'Lower Motor 1'}
        self.set_step_size(distance)
        return instructions[closest_corner], distance

    def set_step_size(self, distance):
        if distance > 50:
            self.step_size = 200
        elif distance > 40:
            self.step_size = 150
        elif distance > 30:
            self.step_size = 100
        elif distance > 20:
            self.step_size = 50
        elif distance > 10:
            self.step_size = 25
        else:
            self.step_size = 10

    @staticmethod
    def get_circle_colour(c, im):
        c = c.astype('int32')
        return np.mean(im[c[1]-c[2]:c[1]+c[2], c[0]-c[2]:c[0]+c[2]])

    def get_centre(self, im):
        circles = images.find_circles(im, 9, 88, 7, 6, 8)
        colours = np.array([self.get_circle_colour(c, im) for c in circles])
        circles = circles[colours < 150]
        self.circles = circles
        return np.mean(circles[:, :2], axis=0)


    def get_frame(self):
        im = self.cam.get_frame()
        im = images.crop_and_mask(im, self.crop, self.mask)
        im = images.bgr_to_gray(im)
        return im





"""-------------------------------------------------------------------------------------------------------------------
Setup external objects
----------------------------------------------------------------------------------------------------------------------"""

def setup_stepper_motors(port = STEPPER_CONTROL):
    """Generate stepper motor controllers for motors on stepper controlled shaker"""    
    ard = arduino.Arduino(port)
    motors = stepper.Stepper(ard)
    return motors

def setup_shaker(init_val=600):
    """This is for the red wishbone spring shaker"""
    myshaker=shaker.Shaker()
    myshaker.set_duty(init_val)
    return myshaker

def setup_camera():
    """This is for using a webcam"""
    cam_num = camera.guess_camera_number()
    cam=camera.Camera(cam_num=cam_num)
    return cam


if __name__ == "__main__":
    #pass
    myshaker = setup_shaker()
    motors=setup_stepper_motors()
    cam=setup_camera()

    balancer = Balancer(cam)#myshaker, motors, cam, centre_pt_fn)
    #balancer.balance(repeats=5, threshold=1)
