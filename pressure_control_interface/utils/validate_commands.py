#!/usr/bin/env python

import os
import yaml
import copy




class CommandValidator:
    def __init__(self, cmd_spec_version, num_channels):

        self.num_channels = num_channels

        this_file = os.path.dirname(os.path.abspath(__file__))
        command_spec_file = os.path.join(this_file,'command_spec', 'commands_'+cmd_spec_version+'.yaml')

        with open(command_spec_file) as f:
            # use safe_load instead of load
            self.cmd_spec = yaml.safe_load(f)
            f.close()
        self.cmd_list = []
        self.generate_command_list()
        self.data_in = None
        self.save_file = None
        self.first_time = None


    def generate_command_list(self):
        cmd_list = []
        for cmd in self.cmd_spec['commands']:
            cmd_list.append(cmd['cmd'])

            cmd['num_args'] = self.get_num_args(cmd)
            
        self.cmd_list = cmd_list
        self.cmd_echo     = self.cmd_spec['echo']
        self.cmd_settings = self.cmd_spec['settings']
        self.cmd_data = self.cmd_spec['data']
        self.cmd_data_types = self.cmd_spec['data']['types'].keys()


    def get_spec(self, cmd):
        cmd = cmd.lower()
        if not cmd in self.cmd_list:
            return None

        cmd_idx = self.cmd_list.index(cmd)

        curr_cmd_spec = self.cmd_spec['commands'][cmd_idx]

        return curr_cmd_spec


    def get_num_args(self, spec):
        num_channels=self.num_channels
        num_args=[0]*2

        if spec is None:
            return None
        
        else:
            num_args_spec = spec['num_args']

            if isinstance(num_args_spec, dict):
                num_args[0] = num_args_spec['min']
                num_args[1] = num_args_spec['max']
            else:
                num_args[0] = num_args_spec
                num_args[1] = num_args_spec
            
            for idx,arg in enumerate(num_args):
                if isinstance(arg, str):
                    if 'num_channels' in arg:
                        num_args[idx] = eval(arg)
        
        return num_args



    def process_line(self, line_in):

        output = None

        if line_in == None:
            return None

        try:
            if line_in.startswith(self.cmd_echo['prefix']):
                #Look for an underscore - This is an echo response
                line_in = line_in.lower()
                line_in=line_in.replace(self.cmd_echo['prefix']+"new ",'')
                line_in=line_in.strip(self.cmd_echo['prefix'])
                line_split = line_in.split(self.cmd_echo['cmd_delimeter'])

                cmd = line_split[0].strip(' ')

                if len(line_split) <= 1:
                    args = ""
                else:
                    args = line_split[1].split(self.cmd_echo['delimeter'])

                echo_in = dict()
                echo_in['_command'] = str(cmd).lower() 
                echo_in['_args'] = args

                return echo_in, 'echo'

            else:
                #All other incomming lines are tab-separated data, where the 
                line_split = line_in.split(self.cmd_data['delimeter'])

                data_type  = int(line_split[1])

                if data_type == 0: # Handle incomming setpoint data
                    # Here marks a new data point. Send the previous one.
                    if self.data_in is not None:
                        #if self.first_time is None:
                        #    self.first_time = copy.deepcopy(self.data_in['time'])

                        #self.data_in['time'] = self.data_in['time'] -self.first_time
                        output = (self.data_in, 'data')

                    # Now begin the next one
                    self.data_in = dict();
                    self.data_in['time'] = int(line_split[0])
                    self.data_in['setpoints'] = [float(i) for i in line_split[2:]]
                elif data_type == 1: # Handle incomming measured data
                    if self.data_in is None:
                        return None

                    if self.data_in['time'] == int(line_split[0]):
                        self.data_in['measured']  = [float(i) for i in line_split[2:]]

                    else:
                        if self.DEBUG:
                            print("COMM_HANDLER: Measured data message not recieved")

                elif data_type == 2: # Handle incomming master pressure data
                    if self.data_in is None:
                        return None

                    if self.data_in['time'] == int(line_split[0]):
                        self.data_in['input_pressure']  = [float(i) for i in line_split[2:]]
            
            return output


        except:
            pass