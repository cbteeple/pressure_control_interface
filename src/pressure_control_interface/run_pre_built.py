#!/usr/bin/env python

import serial
import time
from datetime import datetime
import sys
import os
import yaml
from pynput.keyboard import Key, Listener

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path

data_back=True
save_data = True

# Get the desired save path from save_paths.yaml
traj_folder = get_save_path(which='traj_built')
data_base= get_save_path(which='preferred')
curr_flag_file = os.path.join(traj_folder,"last_sent.txt")


restartFlag = False


class PressureController:
    def __init__(self, devname=None,baudrate=None,serial_hand=None,cycles=1,speed_factor=1.0):
        
        # Initialize the serial handler
        self.sh = CommHandler()
        if serial_hand is not None:
            self.sh = serial_hand
        elif devname is None and baudrate is None:
            self.sh.read_serial_settings()
            self.sh.initialize()
        else:
            self.sh.initialize(devname,baudrate)
            
        self.traj_folder  = traj_folder
        self.speed_factor = speed_factor
        self.cycles      = cycles
        self.save_data = True
        self.data_back = data_back

        # Read in the name of the trajectory that was last sent and create a data output file
        with open(curr_flag_file,'r') as f:
            outfile = f.read()
            f.close()

        if self.save_data:
            self.create_out_file(outfile)

        time.sleep(1)
      
      
    def initialize(self):
        self.sh.send_command('echo',0)
        #self.sh.send_command('load')
        self.sh.send_command('set',[0, 0])
        self.sh.send_command('trajloop',self.cycles, format='%d')
        self.sh.send_command('trajspeed',self.speed_factor)
        self.sh.send_command('mode', 2, format='%d')
        #self.sh.send_command('on')

        time.sleep(2.5)


    def create_out_file(self,filename):
        outFile=os.path.join(data_base,filename)

        dirname = os.path.dirname(outFile)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        i = 0
        while os.path.exists("%s_%04d_00.txt" % (outFile,i) ):
            i += 1

        self.sh.save_init("%s_%04d.txt" % (outFile,i))




            
    def start_traj(self, save=True):
        self.save_data=save
        if self.data_back:
            self.sh.send_command('on')
        
        self.sh.send_command('trajstart')
    

    def stop_traj(self):
        self.sh.send_command('off')
        self.sh.send_command('trajstop')


    def shutdown(self):
        #self.sh.send_command('mode', 3, format='%d')
        #self.sh.send_command('set', [0,0])
        self.stop_traj()
        self.sh.shutdown()

        self.out_file.close()
        
    
    def read_stuff(self):
        line = self.sh.read_line()

        if line is not None:
            print(line)
            if self.save_data:
                self.sh.save_data_line(line)
 





  


if __name__ == '__main__':
    if 1<= len(sys.argv)<=3:
        
        if len(sys.argv)==3:
            speedFact = float(sys.argv[2])
        else:
            speedFact= 1.0

        if len(sys.argv)>=2:
            cycles = int(sys.argv[1])
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
                    
                    if key == Key.esc:
                        exitFlag=True
                        # Stop listener
                        return False
                        
                except KeyboardInterrupt:
                    raise
            
            
            
            listener = Listener(
                on_press=on_press,
                on_release=on_release)
            listener.start()




            # Create a pressure controller object
            pres=PressureController(cycles=cycles,speed_factor=speedFact)

            pres.initialize();
            
            pres.start_traj(save=save_data)
            #pres.read_stuff()
            while True:
                pres.read_stuff()
                if restartFlag is True:
                    pres.start_traj()
                    restartFlag = False
                
        except KeyboardInterrupt:
            listener.stop()
            listener.stop()
            pres.shutdown()
            
    else:
        print("Make sure you sent the right number of arguments")