/* Used serial info from Nick Gammon */

const int PIN = 7;
const unsigned int MAX_INPUT = 50; 
const unsigned int FREQ_DEFAULT = 1000;

void setup() {
  Serial.begin(115200);
  tone(PIN, FREQ_DEFAULT);
}

void process_data (const char * data){
  // Serial.println(data);
  String s = String(data);
  unsigned int duty = s.toInt();
  // Serial.println(duty);
  tone(PIN, FREQ_DEFAULT + duty*15);
  
}

void processIncomingByte (const byte inByte)
  {
  static char input_line [MAX_INPUT];
  static unsigned int input_pos = 0;

  switch (inByte)
    {

    case '\n':   // end of text
      input_line [input_pos] = 0;  // terminating null byte
      
      // terminator reached! process input_line here ...
      process_data (input_line);
      
      // reset buffer for next time
      input_pos = 0;  
      break;

    case '\r':   // discard carriage return
      break;

    default:
      // keep adding if not full ... allow for terminating null byte
      if (input_pos < (MAX_INPUT - 1))
        input_line [input_pos++] = inByte;
      break;

    }  // end of switch
   
  } // end of processIncomingByte  

void loop()
  {
  // if serial data available, process it
  while (Serial.available () > 0)
    processIncomingByte (Serial.read ());
    
  // do other stuff here like testing digital input (button presses) ...

  }  // end of loop
