import common
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

data_files = sorted([os.path.join(path, x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv"])

out_f = os.path.join(path, "lower_bound.out")

first_line = "filename, lower_bound"
lines = [first_line]

for f in data_files:
    filename = os.path.basename(f)
    loaded = common.load_data2(f)
    result = common.moores_single_machine_tardy_jobs_with_slicing(loaded[0], loaded[1])
    lower_bound = len(result[1])

    lines.append("{},{}".format(filename, lower_bound))


ftmp = open(out_f, "w")
ftmp.writelines('\n'.join(lines))
ftmp.close()