import datetime
import time
import os

import numpy as np
import cv2
from scipy import spatial

from labvision import camera, images
from labequipment import arduino, stepper, shaker


STEPPER_CONTROL = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_5573532393535190E022-if00"

class Balancer:

    def __init__(self):
        self.shaker = shaker.Shaker()
        self.shaker.change_duty(600)

        port = STEPPER_CONTROL
        self.ard = arduino.Arduino(port)
        self.motors = stepper.Stepper(self.ard)

        cam_num = camera.guess_camera_number()
        self.cam = camera.Camera(cam_num=cam_num)
        im = self.cam.get_frame()
        self.hex, self.center, self.crop, self.mask = self.find_hexagon(im)
        im = images.crop_and_mask(im, self.crop, self.mask)
        self.im_shape = im.shape
        im = images.draw_polygon(im, self.hex)
        im = images.draw_circle(im, self.center[0], self.center[1], 3)
        images.display(im)

    def balance(self, repeats=5, threshold=10):
        balanced = False
        window = images.Displayer('Levelling')
        center = (0, 0)
        while balanced is False:
            centers = []
            self.shaker.ramp(630, 500, 0.5)
            for f in range(repeats):
                self.f = f
                time.sleep(0.1)
                im = self.get_frame()
                center = self.get_center(im)
                centers.append(center)
            mean_center = np.mean(centers, axis=0)
            instruction, distance = self.find_instruction(mean_center)
            annotated_im = self.annotate_image(im, center, mean_center,
                                               distance, centers)
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

    def annotate_image(self, im, current_center, mean_center, distance,
                       centers):
        im = im.copy()
        if images.depth(im) != 3:
            im = images.gray_to_bgr(im)
        for center in centers:
            im = images.draw_circle(im, center[0], center[1], 5,
                                    images.YELLOW)
        for circle in self.circles:
            im = images.draw_circle(im, circle[0], circle[1], circle[2], images.PINK)
        im = images.draw_circle(im, current_center[0], current_center[1], 5,
                                color=images.ORANGE, thickness=-1)
        im = images.draw_circle(im, self.center[0], self.center[1], 5,
                                images.RED)
        im = images.draw_circle(im, mean_center[0], mean_center[1], 5,
                                images.BLUE)
        font = cv2.FONT_HERSHEY_SIMPLEX
        im = cv2.putText(im, 'Tray Center', (10, 30), font, .5, images.RED, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Current Center', (10, 60), font, .5,
                         images.ORANGE, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Mean Center', (10, 90), font, .5, images.BLUE, 2,
                         cv2.LINE_AA)
        im = cv2.putText(im, 'Pixel distance : {:.3f}'.format(
            distance), (10, 120), font, .5, images.GREEN, 2, cv2.LINE_AA)
        im = cv2.putText(im, 'Repeat: {}'.format(self.f), (10, 150), font, .5,
                         images.GREEN, 2, cv2.LINE_AA)

        im = cv2.putText(im, 'Old Centers', (10, 180), font, .5, images.YELLOW,
                         2, cv2.LINE_AA)
        return im

    def find_instruction(self, center):
        distance = ((center[0] - self.center[0]) ** 2 + (
                     center[1] - self.center[1]) ** 2) ** 0.5
        corner_dists = spatial.distance.cdist(
            np.array(center).reshape(1, 2), self.hex)
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

    def get_center(self, im):
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



    def find_hexagon(self, im):
        res = images.crop_polygon(im)
        crop = res.bbox
        points = res.points
        mask = res.mask
        center = np.mean(points, axis=0)
        return points, center, crop, mask

if __name__ == "__main__":
    balancer = Balancer()
    balancer.balance(repeats=5, threshold=1)
