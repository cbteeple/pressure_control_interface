import os
import sys

# Import a few utility modules
sys.path.insert(1, 'utils')
from parse_data import DataParser
from get_files import get_files_recursively
from get_files import get_save_path


# Get the desired save path from save_paths.yaml
base_path = get_save_path(which='default')

# Set the folder to use within the base data folder
folder = 'example'

# Parse and graph the data, then save it
data_path=os.path.join(base_path, folder)
filenames = get_files_recursively(data_path, filter_extension='.txt')

parser = DataParser(data_path = data_path)
for _, filename_rel, full_filename in filenames:
    print(filename_rel)
    parser.parse_data(filename_rel)
    parser.plot(filename = filename_rel.replace('.txt','.png'),
                ylabel="Pressure (psi)",
                time_from_zero = True)
    parser.save_data(filename_rel.replace('.txt','.pkl'))