import serial
import time
from datetime import datetime
import sys
import os
import yaml
import csv


import validate_commands


class SerialHandler:
    def __init__(self):
        self.serial_settings = None
        self.s = None


    def initialize(self, devname=None, baudrate=None, ser=None):
        if devname is not None and baudrate is not None:
            self.s = serial.Serial(devname,baudrate)
        elif ser is not None:
            self.s = ser
        elif self.serial_settings is not None:
            self.s = serial.Serial(self.serial_settings[0]["devname"], self.serial_settings[0]["baudrate"])
        else:
            self.s = None
            raise ValueError("SerialHandler expects either a devname and baudrate, or and existing serial object")

        self.validator = validate_commands.CommandValidator(self.serial_settings[0]["cmd_spec"])
        self.out_file = None
        self.file_writer = None
        


    # Get serial settings from a file
    def read_serial_settings(self, file=None):
        file_path = os.path.dirname(os.path.realpath(__file__))
        if file is None:
            file=os.path.join(file_path,"..","config","comms","hardware_config.yaml")
        with open(file) as f:
            # use safe_load instead of load
            hardware_settings = yaml.safe_load(f)
            f.close()

        hw_file = hardware_settings.get('hardware')
        devnames = hardware_settings.get('devnames')

        hw_fullfile=os.path.join(file_path,"..","config","hardware",hw_file+".yaml")
        with open(hw_fullfile) as f:
            # use safe_load instead of load
            serial_settings = yaml.safe_load(f)
            f.close()

        for idx, obj in enumerate(serial_settings):
            obj['devname'] = devnames[idx]

        self.serial_settings = serial_settings
        return serial_settings


    # Set serial settings directly
    def get_serial_settings(self):
        return self.serial_settings


    # Set serial settings directly
    def set_serial_settings(self, devname, baudrate):
        self.serial_settings=[{'devname':devname, 'baudrate':baudrate}]


    # Send commands out
    def send_command(self, command, values=None, format="%0.5f"):
        txt = command
        if values is not None:
            print("%s \t %s"%(command, values))
            if isinstance(values, list):
                if values:
                    for val in values:
                        txt+= ";"+format%(val)
            else:
                txt+=";"+format%(values)
        print(txt)
        cmd = txt+'\n'
        self.s.write(cmd.encode())


    # Send a raw string out
    def send_string(self, string, eol='\n'):
        string+=eol
        self.s.write(string.encode())


    # Read one line
    def read_line(self, display=False, raw=False):
        out=None
        if self.s.in_waiting:  # Or: while ser.inWaiting():
            out= self.s.readline().decode().strip()

        if out is not None and display:
            print(out)

        if raw:
            return out
        
        else:
            return self.validator.process_line(out)


    def read_all(self, display=False, raw=False):
        out = []
        while self.s.in_waiting:  # Or: while ser.inWaiting():
            out.append(self.s.readline().decode().strip())

        if len(out) ==0:
            return None
        else:
            if display:
                print(out)

            return out



    def save_init(self, filename, filetype='csv'):
        num_channels = self.serial_settings[0]['num_channels']

        data_to_save = self.validator.cmd_data['types'].keys()
        data_flat_labels = ['time']
        data_labels      = ['time']
        data_lens        = [1]

        for data_type in data_to_save:
            curr_type = self.validator.cmd_data['types'][data_type]

            curr_label = curr_type['label']
            curr_len   = curr_type['length']

            if curr_len == 'num_channels':
                curr_len = num_channels

            data_labels.append(curr_label)
            data_lens.append(curr_len)

            if curr_len>1:
                for idx in range(curr_len):
                    data_flat_labels.append(curr_label+"[%d]"%(idx))
            else:
                data_flat_labels.append(curr_label)


        data_labels.extend(['_command', '_args'])
        data_flat_labels.extend(['_command', '_args'])
        data_lens.extend([1,1])
        self.data_to_save = data_to_save
        self.data_labels = data_labels
        self.data_lens = data_lens
        self.data_flat_labels = data_flat_labels


        self.out_file = open(filename, "w+")
        self.file_writer = csv.writer(self.out_file)
        self.file_writer.writerow(self.data_flat_labels)


    def save_data_line(self,data_line):
            try:
                data=[]
                for idx,key in enumerate(self.data_labels):
                    expected_len = self.data_lens[idx]
                    dat = data_line.get(key,None)
                    if isinstance(dat, list):
                        for curr_dat in dat:
                            data.append(curr_dat)

                        if expected_len > len(dat):
                            for idx in range(expected_len-len(dat)):
                                data.append("")

                        if expected_len < len(dat):
                            print("data array is longer than we expected")

                    elif dat is not None:
                        data.append(dat)
                    else:
                        for idx in range(expected_len):
                            data.append("")
                self.file_writer.writerow(data)
            except IOError:
                print("I/O error")


    def save_raw_line(self, line):
        self.out_file.write(data_line)
            

        


    # Upon shutdown, close the serial instance
    def shutdown(self):
        if self.s is not None:
            self.s.close()
        if self.out_file is not None:
            self.out_file.close()


    # Upon object deletion, shut down the serial handler
    def __del__(self): 
        self.shutdown()