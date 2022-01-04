#!/usr/bin/env python

import serial
import time
import sys
import os
import yaml

from ctrlp import CommHandler
from ctrlp.get_files import get_save_path

# Get the desired save path from save_paths.yaml
config_folder = get_save_path(which='config')


class ConfigSender:
    def __init__(self, devname=None,baudrate=None):
        self.sh = CommHandler()

        if devname is None or baudrate is None:
            self.sh.read_serial_settings()
            self.sh.initialize()
        else:
            self.sh.initialize(devname,baudrate)

        self.config_folder  = config_folder

        time.sleep(2)
        self.sh.send_command("off")
        time.sleep(0.1)
        self.sh.send_command("chan",1)
        time.sleep(0.1)
        self.sh.send_command("mode",0)
        time.sleep(0.1)
        self.sh.send_command("valve",-1)
        time.sleep(0.1)
        self.sh.send_command("valve",-0.001)
        time.sleep(0.1)

        self.sh.read_all(display=True)
            

    # Read the cofniguration from a file
    def read_config(self, filename):
        inFile=os.path.join(self.config_folder,"control",filename+".yaml")

        if os.path.isfile(inFile):
            with open(inFile) as f:
                # use safe_load instead of load
                self.config = yaml.safe_load(f)
                f.close()
        else:
            self.config=None
            print("The config file does not exist")
            self.shutdown()
            

    # Send several configuration settings from a config file
    def set_config(self, filename):
        self.read_config(filename)

        if self.config:
            self.sh.send_command("echo",bool(self.config.get("echo")))
            time.sleep(0.1)
            self.sh.read_all(display=True)

            self.num_channels = self.config.get("channels").get("num_channels")
            time.sleep(0.1)
            self.sh.read_all(display=True)
            
            self.sh.send_command("chan",self.config.get("channels").get("states"))
            time.sleep(0.1)
            self.sh.read_all(display=True)
            

            self.sh.send_command("maxp", self.config.get("max_pressure") )
            time.sleep(0.1)
            self.sh.read_all(display=True)

            self.sh.send_command("minp", self.config.get("min_pressure") )
            time.sleep(0.1)
            self.sh.read_all(display=True)
            
            self.handle_pid()
            
            self.sh.send_command("time",int(self.config.get("data_loop_time")))
            time.sleep(0.1)
            self.sh.read_all(display=True)

            self.sh.send_command("valve",0)
            time.sleep(0.1)
            self.sh.read_all(display=True)
            
            self.sh.send_command("mode",3)
            time.sleep(0.1)
            self.sh.read_all(display=True)
            
            self.sh.send_command("save",[])
            time.sleep(0.1)
            self.sh.read_all(display=True)


    # handle complicated pid settings
    def handle_pid(self):
        pid = self.config.get("PID")

        all_equal = pid.get("all_equal")
        if all_equal:
            values = []
            for idx in range(self.num_channels):
                values.append(pid.get("values"))
        else:
            values = pid.get("values")
            
        # Send out the settings for all channels
        for idx in range(self.num_channels):
            self.sh.send_command("pid",[idx]+values[idx])
            time.sleep(0.1)
            self.sh.read_all(display=True)


    # Shut down the config object
    def shutdown(self):
        self.sh.shutdown()
        
    



if __name__ == '__main__':
    # Create a config object
    pres=ConfigSender()
    if len(sys.argv)==2:
        # Upload the configuration and save it
        pres.set_config(sys.argv[1])
    elif len(sys.argv)==1:        
        # Upload the configuration and save it
        pres.set_config('default')            
    else:
        print("Please include a config file as the input")
    pres.shutdown()