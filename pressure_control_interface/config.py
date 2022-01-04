#!/usr/bin/env python

import serial
import time
import sys
import os
import yaml

from ctrlp import CommHandler, ConfigHandler
from ctrlp.get_files import get_save_path, load_yaml

class ConfigSender:
    def __init__(self, devname=None,baudrate=None):
        self.comm_handler = CommHandler()        

        if devname is None or baudrate is None:
            self.comm_handler.read_serial_settings()
            self.comm_handler.initialize()
        else:
            self.comm_handler.initialize(devname,baudrate)

        self.config_handler = ConfigHandler(self.comm_handler.command_handler)

        self.config_folder  = get_save_path(which='config')
        self.config=None

    # Read the cofniguration from a file
    def load_config(self, filename):
        in_file=os.path.join(self.config_folder,"control",filename+".yaml")
        print(in_file)

        config = self._load_config(in_file)

        if config:
            self.config = self.config_handler.parse_config(config)


    def set_config(self, config):
        if config:
            self.config = self.config_handler.parse_config(config)

            
    def _load_config(self, filename):
        try:
            config = load_yaml(filename)
            if isinstance(config, dict):
                if config.get('channels'):
                    basename = os.path.basename(filename)
                    print('New config "%s" loaded'%(basename))
                    return config
                else:
                    print('Incorrect config format')
                    return False
            else:
                print('Incorrect config format')
                return False
            
        except:
            print('New config was not loaded')
            return False


    def send_config(self, echo=False):
        if self.config:
            commands = self.config_handler.get_commands()
            if echo:
                self.comm_handler.send_command("echo",True)
            for command in commands:
                print(command) 
                if self.comm_handler:
                    self.comm_handler.send_command(command['cmd'],command['args'])
                    time.sleep(0.1)
                    self.comm_handler.read_all(display=True)

            self.comm_handler.send_command('save',None) 

    # Shut down the config object
    def shutdown(self):
        self.comm_handler.shutdown()
        
    



if __name__ == '__main__':
    # Create a config object
    pres=ConfigSender()
    if len(sys.argv)==2:
        # Upload the configuration and save it
        pres.load_config(sys.argv[1])
    elif len(sys.argv)==1:        
        # Upload the configuration and save it
        pres.load_config('default')   
    else:
        print("Please include a config file as the input")
    pres.send_config() 
    pres.shutdown()