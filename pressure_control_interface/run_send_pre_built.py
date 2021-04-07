#!/usr/bin/env python

import serial
import time
from datetime import datetime
import sys
import os
import yaml
from pynput.keyboard import Key, Listener
from send_pre_built import TrajSend
from run_pre_built import PressureController

speedFactor=1.0
dataBack=True
saveData = True
traj_folder = "traj_built"
curr_flag_file = os.path.join("traj_built","last_sent.txt")

board_teensy = True;


restartFlag = False
exitFlag    = False

 


if __name__ == '__main__':
    if 2<= len(sys.argv)<=4:

        if len(sys.argv)==4:
            speedFact = float(sys.argv[3])
        else:
            speedFact= 1.0

        if len(sys.argv)>=3:
            cycles = int(sys.argv[2])
        else:
            cycles = 1
        
        print(cycles)
        print(speedFact)
        
        try:

            def on_press(key):
                try:
                    pass
                except KeyboardInterrupt:
                    raise
            
            
            def on_release(key):
                try:
                    global restartFlag
                    global exitFlag
                    if key == Key.space:
                        print('Restart Trajectory')
                        restartFlag =True
                        print('{0} released'.format( key))
                        print('_RESTART')
                        restartFlag =True
                    
                    if key == Key.ctrl:
                        exitFlag=True
                except KeyboardInterrupt:
                    raise
            
            
            listener = Listener(
                on_press=on_press,
                on_release=on_release)
            listener.start()

            
            # Create a pressure controller object
            traj=TrajSend()
            traj.board_teensy=board_teensy
            traj.get_traj(sys.argv[1])

            traj.speedFactor = speedFact

            # Upload the trajectory and start it
            traj.send_traj()
            traj.sh.read_line()



            # Create a pressure controller object
            pres=PressureController(serial_hand = traj.sh, cycles=cycles,speed_factor=speedFact)

            
            pres.start_traj()
            #pres.sh.read_line()
            while True:
                pres.sh.read_line(display=True)
                if restartFlag is True:
                    pres.start_traj()
                    restartFlag = False
                
                if exitFlag:
                    listener.stop()
                
        except KeyboardInterrupt:
            listener.stop()
            listener.stop()
            pres.shutdown()
            
    else:
        print("Please include the filename as the input argument")