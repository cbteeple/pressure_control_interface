#include <stdlib.h>
#include "Arduino.h"
#include "handleSerialCommands.h"
#include "sensorSettings.h"

//_________________________________________________________
//PUBLIC FUNCTIONS
bool handleSerialCommands::go(sensorSettings &settings){
  bool newCommand = getCommand();
  bool newSettings = false;
  if (newCommand){
    newSettings=processCommand(settings);
  }
  return newSettings;
}

void handleSerialCommands::startBroadcast(){
  broadcast=true;
}

void handleSerialCommands::stopBroadcast(){
  broadcast=false;
}


void handleSerialCommands::initialize(int num){
  numSensors=num;
}


//_________________________________________________________
//PRIVATE FUNCTIONS

bool handleSerialCommands::getCommand(){
  if (Serial.available() > 0) {
    command = Serial.readStringUntil('\n');
    command.toUpperCase();
    return true;
  }
  else{
    return false;
  }
}




bool handleSerialCommands::processCommand(sensorSettings &settings){
  bool newSettings=false;
  if (broadcast){
    Serial.print("_");
  }
  if(command.startsWith("OFF")){
    settings.outputsOn = false;
    if (broadcast){
      Serial.print("Output: OFF");
    }
  }
  else if(command.startsWith("ON")){ 
    settings.outputsOn = true;
    if (broadcast){
      Serial.print("Output: ON");
    }
  }
  else if (command.startsWith("TIME")){
    if(getStringValue(command,';',1).length()){
      settings.looptime = getStringValue(command,';',1).toInt();
      newSettings=true;
      if (broadcast){
        Serial.print("NEW ");
      }
    }
    if (broadcast){
      Serial.print("Loop Time: ");
      Serial.print(settings.looptime);
    }
  }
  else if(command.startsWith("SET")){
    if(getStringValue(command,';',numSensors).length()){
      for (int i=0; i<numSensors; i++){
        settings.setpoints[i]= getStringValue(command,';',i+1).toFloat();
      }
      newSettings=true;
      if (broadcast){
        Serial.print("NEW ");
      }
    }
    else if(getStringValue(command,';',1).length()){
      float allset=getStringValue(command,';',1).toFloat();
      for (int i=0; i<numSensors; i++){
        settings.setpoints[i]= allset;
      }
      newSettings=true;
      if (broadcast){
        Serial.print("NEW ");
      }
    }
    if (broadcast){
      Serial.print("SETPOINT: ");
      for (int i=0; i<numSensors; i++){
        Serial.print(settings.setpoints[i],4);
        Serial.print('\t');
      }
    }
  }
  else if(command.startsWith("WINDOW")){
     if(getStringValue(command,';',numSensors).length()){
      for (int i=0; i<numSensors; i++){
        settings.deadzones[i]=getStringValue(command,';',i+1).toFloat();
      }
      newSettings=true;
      if (broadcast){
        Serial.print("NEW ");
      }
     
     }
    if (broadcast){
      Serial.print("WINDOW: ");
      for (int i=0; i<numSensors; i++){
        Serial.print(settings.deadzones[i],4);
        Serial.print('\t');
      }
    }
     
  }
  else {
    newSettings=false;
    if (broadcast){
      Serial.print("Unrecognized Command");
    }
  }

  if (broadcast){
    Serial.print("\n");
  }

  return newSettings;
}




String handleSerialCommands::getStringValue(String data, char separator, int index)
{
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length()-1;

  for(int i=0; i<=maxIndex && found<=index; i++){
    if(data.charAt(i)==separator || i==maxIndex){
        found++;
        strIndex[0] = strIndex[1]+1;
        strIndex[1] = (i == maxIndex) ? i+1 : i;
    }
  }

  return found>index ? data.substring(strIndex[0], strIndex[1]) : "";
}



