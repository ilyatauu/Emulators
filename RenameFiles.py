import sys
import os
import re

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


files = [x for x in os.listdir(path) if os.path.splitext(x)[1] == ".out"]

for f in files:
    x = f[13:14]
    i = int(x)+5
    new_f = f.replace("_" + x + ".", "_" + repr(i) + ".")
    os.rename(os.path.join(path, f),os.path.join(path, new_f))


