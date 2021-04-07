import os
import yaml

# Recursively get all files with a specific extension, excluding a certain suffix
def get_files_recursively(start_directory, filter_extension=None):
    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if filter_extension is None or file.lower().endswith(filter_extension):
                yield (root, file, os.path.abspath(os.path.join(root, file)))


def get_save_path(filename="save_paths.yaml", which=None):
    # Get the base path for data from save_paths.yaml
    with open(filename) as f:
        save_paths = yaml.safe_load(f)

    if which is None:
        data_base = save_paths['preferred']
        if not os.path.exists(data_base):
            print("PREFERRED SAVE PATH NOT FOUND: %s"%(data_base))
            data_base = save_paths['default']
            if os.path.exists(data_base):
                print("Using default save path: %s"%(data_base))
            else:
                print("DEFAULT SAVE PATH NOT FOUND: %s"%(data_base))
                print("Using empty save path")
                data_base = ""
    else:
        data_base = save_paths.get(which)
    
    return data_base