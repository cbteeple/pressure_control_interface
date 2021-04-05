#!/usr/bin/env python

import sorotraj
import os
import sys

sys.path.insert(1, 'utils')
from get_files import get_save_path

# Get the desired save path from save_paths.yaml
setup_location = get_save_path(which='traj_setup')
build_location = get_save_path(which='traj_built')



if __name__ == '__main__':
    if len(sys.argv)==2:
        traj = sorotraj.TrajBuilder()
        traj.load_traj_def(os.path.join(setup_location,sys.argv[1]))
        traj.save_traj(os.path.join(build_location,sys.argv[1]))

    else:
        print('make sure you give a filename')
        
        
        
        
        
        