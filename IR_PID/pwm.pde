// HeaterControl
// Adapted for Surface Mount Soldering with a Hot Plate
// Jim Larson
// Jan 2010
//
// Original work by (and all credit to):
// Tim Hirzel 
// Dec 2007
// 
// This file is for controlling a heater via a solid state zero crossing relay
// since these are zero-crossing relays, it makes sense to just match my local
// AC frequency, 60hz
//
// This code is hard wired to a period of 1 second and the duty cycle goes from
// 0 to 100% int steps of 1ms.  note: the AC current crosses zero every 8.33ms
// values less than the Nyquist (16.66ms) may not behave as expected.
//
// All code released under
// Creative Commons Attribution-Noncommercial-Share Alike 3.0 
//----------------------------------------------------------------
// Define here the pin used for the control output to the Hot Plate
//  AC controller. Any digital output pin can be used.
#define HEAT_RELAY_PIN PIN_D6
//----------------------------------------------------------------

float heatcycles; // the number of millis out of 1000 for the current heat amount (percent * 10)

boolean heaterState = 0;

unsigned long heatCurrentTime, heatLastTime;

void setupHeater() {
  pinMode(HEAT_RELAY_PIN , OUTPUT);
}


void updateHeater() {
  boolean h;
  heatCurrentTime = millis();
  if(heatCurrentTime - heatLastTime >= 1000 or heatLastTime > heatCurrentTime) { //second statement prevents roll over / overflow errors
    _turnHeatElementOnOff(1);  // begin cycle
    heatLastTime = heatCurrentTime;   
  } 
  if (heatCurrentTime - heatLastTime >= heatcycles) {
    _turnHeatElementOnOff(0);
  }
}

void setHeatPowerPercentage(float power) {
  if (power <= 0.0) {
    power = 0.0;
  }	
  if (power >= 1000.0) {
    power = 1000.0;
  }
  heatcycles = power;
}

float getHeatCycles() {
  return heatcycles;
}

void _turnHeatElementOnOff(boolean on) {
  digitalWrite(HEAT_RELAY_PIN, on);	//turn pin high
  heaterState = on;
}

// End Heater Control
