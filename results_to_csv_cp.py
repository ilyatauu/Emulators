import os
import sys
import re



if len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    # Raw_input is used to collect data from the user
    base_path = raw_input('> ')
else:
    base_path = sys.argv[0]

if os.path.isdir(base_path) is False:
    print base_path + ", is not a directory, exit or enter directory name"
    base_path = raw_input('> ')

dir_list = ["CP_1s", "CP_2s", "CP_5s", "CP_10s", "CP_20s"]
for d in dir_list:
    path = os.path.join(base_path, d)
    for f in os.listdir(path):
        newf = f.replace("_limit1s", "")
        newf = newf.replace("_limit2s", "")
        newf = newf.replace("_limit5s", "")
        newf = newf.replace("_limit10s", "")
        newf = newf.replace("_limit20s", "")
        os.rename(os.path.join(base_path, d, f), os.path.join(base_path, d,newf))


