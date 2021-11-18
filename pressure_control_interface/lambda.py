#!/usr/bin/env python

import numpy as np
import time
import os
import sys

sys.path.insert(1, 'utils')
from comm_handler import CommHandler
from get_files import get_save_path


def send_pressure(pressures):
    cmd=[sampling_rate]
    cmd.extend(pressures)
    #print(curr_pressures)
    ctrlp.send_command("set",cmd)

end_time = 10 # [sec]
sampling_rate = 0.1 # [sec]

trajectory= lambda time: [
    15*np.sin(time*(2*np.pi) + 0.0*np.pi) + 15,
    15*np.sin(time*(2*np.pi) + 0.0*np.pi) + 15,
    15*np.sin(time*(2*np.pi) + 0.25*np.pi) + 15,
    15*np.sin(time*(2*np.pi) + 0.25*np.pi) + 15,
    15*np.sin(time*(2*np.pi) + 0) + 15,
    15*np.sin(time*(2*np.pi) + 0) + 15,
    15*np.sin(time*(2*np.pi) + 0) + 15,
    15*np.sin(time*(2*np.pi) + 0) + 15,
    15*np.sin(time*(2*np.pi) + 0) + 15,
    ]


ctrlp = CommHandler()
ctrlp.read_serial_settings()
ctrlp.initialize()

last_time = time.time()
curr_time = time.time()
curr_time_rel = curr_time-last_time
while(curr_time_rel<end_time):
    curr_time = time.time() 
    curr_time_rel = curr_time-last_time
    curr_pressures = trajectory(curr_time_rel)

    send_pressure(curr_pressures)
    time.sleep(sampling_rate)

send_pressure([0]*9)
    


