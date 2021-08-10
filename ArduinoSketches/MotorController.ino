#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"

Adafruit_MotorShield AFMS = Adafruit_MotorShield();

Adafruit_DCMotor *myMotor1 = AFMS.getMotor(1); // Green
Adafruit_DCMotor *myMotor2 = AFMS.getMotor(2); // Orange
Adafruit_DCMotor *myMotor3 = AFMS.getMotor(3); // Blue

String command;

int RedUpPin = 4; //forward/backward buttons
int YellowDownPin = 2; 
int GreenPin = 12; //on/off buttons for each motor
int BluePin = 7;
int OrangePin = 8;

int state1 = 0; //all motors initially off
int state2 = 0;
int state3 = 0;

int buttonOld1 = LOW;
int buttonOld2 = LOW;
int buttonOld3 = LOW;

int GreenLightPin = 6;
int BlueLightPin = 10;
int OrangeLightPin = 13;
int RedUpLightPin = 11;
int YellowDownLightPin = 9;

int serialforward1;
int serialbackward1;
int serialforward2;
int serialbackward2;
int serialforward3;
int serialbackward3;
int serialforwardall;
int serialbackwardall;


void setup() {
  AFMS.begin();

  myMotor1->setSpeed(500); //motor speeds
  myMotor2->setSpeed(500);
  myMotor3->setSpeed(500);
  
  pinMode(RedUpPin, INPUT_PULLUP); //forwards/backwards buttons
  pinMode(YellowDownPin, INPUT_PULLUP);
  
  pinMode(GreenPin, INPUT_PULLUP); //om/offbuttons for each motor
  pinMode(BluePin, INPUT_PULLUP);
  pinMode(OrangePin, INPUT_PULLUP);
  
  pinMode(GreenLightPin, OUTPUT);
  pinMode(BlueLightPin, OUTPUT);
  pinMode(OrangeLightPin, OUTPUT);
  pinMode(RedUpLightPin, OUTPUT);
  pinMode(YellowDownLightPin, OUTPUT);
  
  Serial.begin(9600);

  Serial.println("ready");
}

void loop() 
{
  if(Serial.available()){ //allows motors to be controlled through serial commands
    command = Serial.readStringUntil('\n');
    serialcomm(serialforward1, serialbackward1, state1, "1");

    serialcomm(serialforward2, serialbackward2, state2, "2");

    serialcomm(serialforward3, serialbackward3, state3, "3");
  }
  
  serialforwardall = serialforward1+serialforward2+serialforward3;
  serialbackwardall = serialbackward1+serialbackward2+serialbackward3;
  
  mc(GreenPin, buttonOld1, state1, GreenLightPin, 1); //allows motors to be controlled by buttons
  
  mc(BluePin, buttonOld2, state2, BlueLightPin, 2);

  mc(OrangePin, buttonOld3, state3, OrangeLightPin, 3);
}


int leftright(int i){
  Adafruit_DCMotor *motor = AFMS.getMotor(i);
  if (digitalRead(RedUpPin) == HIGH || serialforwardall != 0) //if forward button pressed, run forward
  {
  digitalWrite(RedUpLightPin, HIGH);
    motor->run(FORWARD);
  }
  else if (digitalRead(YellowDownPin) == HIGH || serialbackwardall != 0)
  {
    digitalWrite(YellowDownLightPin, HIGH);
    motor->run(BACKWARD);
  }
  else
  {
    digitalWrite(RedUpLightPin, LOW);
    digitalWrite(YellowDownLightPin, LOW);
    motor->run(RELEASE);
  }
}


void mc(int buttonPin, int &buttonOld, int &state, int light,  int j) {
  
  Adafruit_DCMotor *motor = AFMS.getMotor(j);
  
  int buttonNew=digitalRead(buttonPin);
  
  if(buttonOld==LOW && buttonNew==HIGH) //button is pressed
  {
    if (state==0)
    {
      state=1; //if device is off turn it on
    }
    else
    {
      state=0; //if device is on turn it off
    }
    buttonOld = HIGH; //buttonNew becomes buttonOld as loop runs again
  }
  else if(buttonNew==LOW && buttonOld==HIGH) //button is released
  {
    buttonOld = LOW;
  }
  else //button is held down or not pressed at all
  {
    if(state==1) //if device is on
    {
      digitalWrite(light, HIGH);
      int leftrightj;
      leftrightj = leftright(j);
    } 
    else //if device is off stop motor
    {
      digitalWrite(light, LOW);
      digitalWrite(RedUpLightPin, LOW);
      digitalWrite(YellowDownLightPin, LOW);
      motor->run(RELEASE);
    } 
  }
}

void serialcomm(int &serialforward, int &serialbackward, int &state, String k) {    
    
    if(command.equals(k + "f")){
        state=1;
        serialforward = 1;
        serialbackward = 0;
        Serial.println("Motor " + k + " is on and running forwards");
    }
    else if(command.equals(k + "b")){
        state=1;
        serialbackward = 1;
        serialforward = 0;
        Serial.println("Motor " + k + " is on and running backwards");
    }
    else if(command.equals(k + "stop")){
        state=0;
        serialforward = 0;
        serialbackward = 0;
        Serial.println("Motor " + k + " is off");
    }
}
