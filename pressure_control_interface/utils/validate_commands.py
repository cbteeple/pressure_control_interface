#!/usr/bin/env python

import os
import yaml




class CommandValidator:
    def __init__(self, cmd_spec_version):

        

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


    def generate_command_list(self):
        cmd_list = []
        for cmd in self.cmd_spec['commands']:
            cmd_list.append(cmd['cmd'])
            
        self.cmd_list = cmd_list
        self.cmd_echo     = self.cmd_spec['echo']
        self.cmd_settings = self.cmd_spec['settings']
        self.cmd_data = self.cmd_spec['data']
        self.cmd_data_types = self.cmd_spec['data']['types'].keys()



    def process_line(self, line_in):
        if not line_in:
            return False

        try:
            if line_in.startswith(self.cmd_echo['prefix']):
                #Look for an underscore - This is an echo response
                line_in=line_in.replace(self.cmd_echo['prefix']+"NEW ",'')
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
                        return self.data_in, 'data'

                    # Now begin the next one
                    self.data_in = dict();
                    self.data_in.time = int(line_split[0])
                    self.data_in.setpoints = [float(i) for i in line_split[2:]]

                elif data_type == 1: # Handle incomming measured data
                    if self.data_in is None:
                        return

                    if self.data_in.time == int(line_split[0]):
                        self.data_in.measured  = [float(i) for i in line_split[2:]]

                    else:
                        if self.DEBUG:
                            print("COMM_HANDLER: Measured data message not recieved")

                elif data_type == 2: # Handle incomming master pressure data
                    if self.data_in is None:
                        return

                    if self.data_in.time == int(line_split[0]):
                        self.data_in.input_pressure  = [float(i) for i in line_split[2:]]


        except rospy.ROSException:
            return