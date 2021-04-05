#!/usr/bin/env python

import time
import sys
import os
import pickle
import yaml
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import seaborn as sns
from cycler import cycler
from get_files import get_save_path

pal0 = sns.color_palette('pastel')
pal1 = sns.color_palette('bright')
pal2 = sns.color_palette('dark')
plt.rcParams["font.family"] = "arial"
plt.rcParams["font.size"] = 12


# Get the base path for data from save_paths.yaml
with open("save_paths.yaml") as f:
    save_paths = yaml.safe_load(f)

data_base = save_paths['preferred']
if not os.path.exists(data_base):
    data_base = save_paths['default']
    if not os.path.exists(data_base):
        data_base = ""


# Define the data parser
class DataParser:
    def __init__(self, data_path = data_base):
        # set up stuff
        self.data_path = data_path
    

    def _reset_data(self):
        self.echo = []
        self.setpoint = {'time': [], 'value':[]}
        self.measured = {'time': [], 'value':[]}
        self.master_pressure = {'time': [], 'value':[]}


    # Read in the raw data
    def _load_raw_data(self, filename):
        fulfile=os.path.join(self.data_path,filename)
        # If filename exists, open it
        with open(fulfile,'r') as f:
            line = f.readline()
            while line:
                line = line.strip()
                self._parse_line(line)
                line = f.readline()
            

    # Parse one line of the data
    def _parse_line(self, line):
        # If first character is underscore, store that in the "echo" list
        if line[0] == '_':
            self.echo.append(line[1:])
        
        # Else - the line must contain data
        else:
            # Split line by tabs and parse
            line_vec = line.split('\t')
            time_ms = int(line_vec[0])
            time_sec = float(time_ms)/1000.0
            data_type = int(line_vec[1])
            data = [float(x) for x in line_vec[2:]]

            # If second item is 0, store the rest of the line in "setpoint" list
            if data_type ==0 and data:
                self.setpoint['time'].append(time_sec)
                self.setpoint['value'].append(data)

            # Elif second item is 1, store the rest of the line in "measured" list
            elif data_type ==1 and data:
                self.measured['time'].append(time_sec)
                self.measured['value'].append(data)

            # Elif second item is 2, store the rest of the line in "master_pressure" list
            elif data_type ==2 and data:
                self.master_pressure['time'].append(time_sec)
                self.master_pressure['value'].append(data)
            

        # Plot one data set
    def _plot_one(self, data, palette=pal1, time_from_zero=False, **kwargs):
        data_np=self._to_nparray(data)
        if time_from_zero:
                time_offset = data_np['time'][0]
        else:
            time_offset = 0
        plt.gca().set_prop_cycle(plt.rcParams['axes.prop_cycle'])
        plt.gca().set_prop_cycle(color = palette)
        plt.plot(data['time']-time_offset, data['value'],**kwargs)


    # Convert one data set to numpy arrays
    def _to_nparray(self, field):
        out = dict()
        for key in field:
            out[key] = np.array(field[key])
        return out


    # Set the data path directly
    def set_data_path(self, path):
        self.data_path = path


    # Parse data from a file
    def parse_data(self, filename):
        self._reset_data()
        if isinstance(filename, str):
            # Read the data from a file
            in_data=None
            if filename[-4:] == '.pkl':
                with open(fullfile,'r') as f:
                    in_data = pickle.load(f)

            elif filename[-5:] == '.yaml':
                with open(fullfile,'r') as f:
                    in_data = yaml.safe_load(f)

            elif filename[-4:] == '.csv':
                print("CSV Save is not implemented yet")
                #out = []
                #with open(fullfile,'w') as f:
                #    np.savetxt(f, out, delimiter=",")

            elif filename[-4:] == '.txt':
                # open the data file and parse it
                self._load_raw_data(filename)

            if in_data is not None:
                self.echo     = in_data['echo']
                self.setpoint = in_data['setpoint']
                self.measured = in_data['measured']
                self.master_pressure = in_data['master_pressure']

        else:
            print("ERROR: Please give the data parser one filename or a list of filenames")

    # Plot the data all on one graph
    def plot(self, filename=None, ylabel="Data", time_from_zero = False, show = False):
        plt.figure()
         
        if self.setpoint['time']:
            self._plot_one(self.setpoint, palette=pal0, time_from_zero=time_from_zero,
                           linewidth=0.5, linestyle='--')

        if self.measured['time']:
            self._plot_one(self.measured, palette=pal1, time_from_zero=time_from_zero,
                           linewidth=1.0, linestyle='-')

        if self.master_pressure['time']:
            self._plot_one(self.master_pressure, palette=pal2, time_from_zero=time_from_zero,
                           linewidth=1.0, linestyle='-')
        
        plt.xlabel('Time (sec)')
        plt.ylabel(ylabel)

        if filename is not None:
            fullfile = os.path.join(self.data_path,filename)
            plt.savefig(fullfile,dpi=300)

        if show:
            plt.show()
        
        plt.close()


    # Save parsed data into a file
    def save_data(self, filename):
        fullfile = os.path.join(self.data_path,filename)
        out = dict()
        out['echo'] = self.echo
        out['setpoint'] = self.setpoint
        out['measured'] = self.measured
        out['master_pressure'] = self.master_pressure

        # Save the data in a file
        if filename[-4:] == '.pkl':
            with open(fullfile,'wb') as f:
                pickle.dump(out,f)

        elif filename[-5:] == '.yaml':
            with open(fullfile,'w') as f:
                yaml.dump(out,f,default_flow_style=False )

        elif filename[-4:] == '.csv':
            print("CSV Save is not implemented yet")
            #out = []
            #with open(fullfile,'w') as f:
            #    np.savetxt(f, out, delimiter=",")
