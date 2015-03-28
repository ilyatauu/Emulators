import sys
import os

# ************* Main Program ************************
if len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    # Raw_input is used to collect data from the user
    path = raw_input('> ')
else:
    path = sys.argv[0]

if os.path.isdir(path) is False:
    print path + ", is not a directory, exit or enter directory name"
    path = raw_input('> ')


files = os.listdir(path)

for f in files:
    new_f = f.replace("d20", "d20p20")
    os.rename(os.path.join(path, f),os.path.join(path, new_f))


