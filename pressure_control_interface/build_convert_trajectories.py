import sorotraj
import os

from ctrlp.get_files import get_save_path

folder = 'palm'
files_to_use = ['rot_gait','translate']


# Get the desired save path from save_paths.yaml
setup_base = get_save_path(which='traj_setup')
build_base = get_save_path(which='traj_built')

setup_location = os.path.join(setup_base,folder)
build_location = os.path.join(build_base,folder)

# Define a line-by-line conversion function to use
#   This example converts from orthogonal axes to differential actuation.
def linear_conversion(traj_line, weights):
    traj_length=len(traj_line)-1

    traj_line_new = [0]*(traj_length+1)
    traj_line_new[0]=traj_line[0] # Use the same time point

    for idx in range(int(traj_length/2)):
        idx_list = [2*idx+1, 2*idx+2]
        traj_line_new[idx_list[0]] = weights[0]*traj_line[idx_list[0]] + weights[1]*traj_line[idx_list[1]] 
        traj_line_new[idx_list[1]] = weights[0]*traj_line[idx_list[0]] - weights[1]*traj_line[idx_list[1]]

    return traj_line_new


# Set up the specific version of the conversion function to use
weights = [0.9, 1.0]
conversion_fun = lambda line: linear_conversion(line, weights)

# Build the trajectories, convert them , and save them
traj = sorotraj.TrajBuilder(graph=False)
for file in files_to_use:
    traj.load_traj_def(os.path.join(setup_location,file))
    traj.save_traj(os.path.join(os.path.abspath(build_location),file+'_orig'))
    traj.convert(conversion_fun)
    traj.save_traj(os.path.join(os.path.abspath(build_location),file))
    traj.plot_traj()