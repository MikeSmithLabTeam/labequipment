#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"

Adafruit_MotorShield AFMS = Adafruit_MotorShield();  // Create an instance of the Adafruit Motor Shield
Adafruit_StepperMotor *stepper1 = AFMS.getStepper(200, 1);  // Stepper motor 1 object
Adafruit_StepperMotor *stepper2 = AFMS.getStepper(200, 2);  // Stepper motor 2 object

void setup() {
  Serial.begin(115200);  // Set the baud rate to match your serial 
  Serial.setTimeout(1000);
  AFMS.begin();  // Initialize the Adafruit Motor Shield
  stepper1->setSpeed(27000);  // Set the initial speed for stepper motor 1 (adjust as needed)
  stepper2->setSpeed(27000);  // Set the initial speed for stepper motor 2 (adjust as needed)
  Serial.println("ready");  // Print the received command
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');  // Read the incoming serial command

    if (command.startsWith("h") || command.startsWith("H")){
      Serial.println("Format : M1+1000 where:\n M=Motor\n 1= Motor 1\n+=FORWARD\n1000 is the number of steps");  // Print the received command
    }

    // Process the command and control the motors accordingly
    if (command.startsWith("M1+")) {
      int steps = command.substring(3).toInt();
      Serial.println("Received: " + command);  // Print the received command
      stepper1->step(steps, FORWARD, MICROSTEP);
      stepper1->release();
    } else if (command.startsWith("M1-")) {
      int steps = command.substring(3).toInt();
      Serial.println("Received: " + command);  // Print the received command
      stepper1->step(steps, BACKWARD, MICROSTEP);
      stepper1->release();
    } else if (command.startsWith("M2+")) {
      int steps = command.substring(3).toInt();
      Serial.println("Received: " + command);  // Print the received command
      stepper2->step(steps, FORWARD, MICROSTEP);
      stepper2->release();
    } else if (command.startsWith("M2-")) {
      int steps = command.substring(3).toInt();
      Serial.println("Received: " + command);  // Print the received command
      stepper2->step(steps, BACKWARD, MICROSTEP);
      stepper2->release();
    } else {
      Serial.println("Command not recognised. Type h for help");
    } 
  }
}