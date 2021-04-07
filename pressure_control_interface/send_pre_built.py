#!/usr/bin/env python

import serial
import time
import sys
import os
import yaml

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path

# Get the desired save path from save_paths.yaml
traj_folder = get_save_path(which='traj_built')
curr_flag_file = os.path.join(traj_folder,"last_sent.txt")


restartFlag = False
board_teensy= True



class TrajSend:
    def __init__(self, devname=None,baudrate=None):
        self.sh = CommHandler()

        if devname is None or baudrate is None:
            self.sh.read_serial_settings()
            self.sh.initialize()
        else:
            self.sh.initialize(devname,baudrate)

        self.traj_folder  = traj_folder
        self.send_wait = 0.05;
        self.board_teensy= board_teensy

        time.sleep(0.5)

        self.sh.send_command("echo",1)

        
        time.sleep(0.5)
        for i in range(50):
            self.sh.read_line(display=True)
            #time.sleep(0.05)

    # Read in the trajectory and store it in a list of arrays
    def get_traj(self,filename):
        self.filename = filename
        # Read in the setpoint file
        inFile=os.path.join(traj_folder,filename+".traj")
        with open(inFile,'r') as f:
            # use safe_load instead of load
            trajIn = yaml.safe_load(f)
            f.close()


        # Get data from the file
        #self.settings = trajIn.get("settings")
        self.traj = trajIn.get("setpoints")
        self.prefix = trajIn.get("prefix",None)
        self.suffix = trajIn.get("suffix",None)
        self.wrap = trajIn.get("wrap",False)
        


    def write_traj_out(self, traj, traj_type="main"):
        num_channels=len(traj[0])
        
        if traj_type is "prefix":
            cmd_type="prefset";
        elif traj_type is "suffix":
            cmd_type="suffset";
        else:
            cmd_type="trajset";
                
        for idx, entry in enumerate(traj):
            # Send a string to the pressure controller
                                   
            #string=(cmd_type+";%d;%0.3f")%(idx, entry[0]);
            #for i in range(num_channels-1):
            #    string+=";%0.3f" %(entry[i+1])
            #print(string)
            #self.s.write(string+'\n')
            entry.insert(0,idx)
            self.sh.send_command(cmd_type,entry)
            
            time.sleep(0.05)
            
            if not self.board_teensy:
                time.sleep(0.5)
                for i in range(3):
                    self.sh.read_line(display=True)
                    time.sleep(self.send_wait)


    def send_traj(self):
        lastTime = 0.0
        pre_len=0
        suf_len=0
        if self.prefix is not None:
            pre_len = len(self.prefix)
        if self.suffix is not None:
            suf_len = len(self.suffix)


        self.sh.send_command('trajconfig',[pre_len,len(self.traj),suf_len,1.0], format='%d')
            
        for i in range(3):
            self.sh.read_line(display=True)
            time.sleep(0.05)
        self.write_traj_out(self.traj,   "main")
        if self.prefix is not None:
            self.write_traj_out(self.prefix, "prefix")
            
        if self.suffix is not None:
            self.write_traj_out(self.suffix, "suffix")

        self.sh.send_command('trajset')
           
            
        dirname = os.path.dirname(curr_flag_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        self.out_file = open(curr_flag_file, "w+")
        self.out_file.write(self.filename)
        self.out_file.close()
            

    def shutdown(self):
        #self.s.write("mode;3"+'\n')
        #self.s.write("set;0;0"+'\n')
        self.sh.shutdown()
    


  


if __name__ == '__main__':
    if 2<= len(sys.argv)<=2:

        
        try:
            

            # Create a pressure controller object
            pres=TrajSend()
            pres.get_traj(sys.argv[1])



            # Upload the trajectory and start it
            pres.send_traj()
            
            for i in range(50):
                pres.sh.read_line(display=True)
            pres.shutdown()
            
                
        except KeyboardInterrupt:
            pres.shutdown()
            
    else:
        print("Please include the filename as the input argument")