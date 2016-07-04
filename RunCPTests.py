import sys
import os
import common
import Layout
import RPFGuan
import TBased
import csv
import cpbased


def get_path_from_user():
    if len(sys.argv) < 2:
        print 'Please enter directory with problems data'
        # Raw_input is used to collect data from the user
        path = raw_input('> ')
    else:
        path = sys.argv[1]

    if not os.path.isdir(path):
        print path + ", is not a directory, exit or enter directory name"
        path = raw_input('> ')

    return path

def solve_and_save(fullfilename, cp_dir, seconds_limit):
    if not os.path.exists(cp_dir):
        os.mkdir(cp_dir)

    filename = os.path.basename(fullfilename)
    file_out = os.path.join(cp_dir, filename + ".out")
    
    if os.path.exists(file_out):
        return

    problem_data = common.load_data2(fullfilename)
    solver = cpbased.EmulatorsCpSolver()
    solver.total_penalty_lower_bound = None
    solver.time_limit = seconds_limit
    result = solver.solve_penalty_only(problem_data[0],problem_data[1])
    # result = solver.solve(problem_data[0],problem_data[1])
    print "Objective value: " + `result.objective_value`

    file_out = os.path.join(cp_dir, filename + ".out")
    print("Writing to file: " + file_out)
    outf = open(file_out, "w")

    if result.optimal:
        optimal_int = 1
    else:
        optimal_int = 0

    if not result.feasible:
        output = ["-1," + `optimal_int`] + ["\n"]
    else:
        output = [`result.objective_value` + ","+ `optimal_int` + "," + `result.total_run_time`] + ["\n"]
    
    outf.writelines(output)
    outf.flush()
    outf.close()

def solve_path(path):
    data_files = sorted([os.path.join(path, x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv"
                         and not x.startswith("result")])
    cp_dir = os.path.join(path, "CP")
    if not os.path.exists(cp_dir):
        os.mkdir(cp_dir)

    for f in data_files:
        pass
        # filename = os.path.basename(f)

        # if "m15j30" in f:
        #     continue

        # if "m15" not in f:
        #     continue

        # solve_and_save(f, cp_dir + "_1s", 1)
        # solve_and_save(f, cp_dir + "_2s", 1)
        # solve_and_save(f, cp_dir + "_5s", 5)
        # solve_and_save(f, cp_dir + "_10s", 10)
        # solve_and_save(f, cp_dir + "_20s", 20)
        # solve_and_save(f, cp_dir + "_50s", 50)
        # solve_and_save(f, cp_dir + "_100s", 100)
        # solve_and_save(f, cp_dir + "_200s", 200)
        # solve_and_save(f, cp_dir + "_400s", 400)
        # solve_and_save(f, cp_dir + "_800s", 800)
        # solve_and_save(f, cp_dir + "_1200s", 1200)
        # solve_and_save(f, cp_dir + "_1800s", 1800)
        # solve_and_save(f,cp_dir+"_40s", 40)
    for f in data_files:
        solve_and_save(f, cp_dir + "_1s", 1)

    for f in data_files:
        solve_and_save(f, cp_dir + "_5s", 5)

    for f in data_files:
        solve_and_save(f, cp_dir + "_10s", 10)

    for f in data_files:
        solve_and_save(f, cp_dir + "_20s", 20)

    for f in data_files:
        solve_and_save(f, cp_dir + "_50s", 50)

    for f in data_files:
        solve_and_save(f, cp_dir + "_0s", 100)
    # for f in data_files:
    #     solve_and_save(f, cp_dir + "_400s", 400)

    # for f in data_files:
    #     solve_and_save(f, cp_dir + "_800s", 800)

    # for f in data_files:
    #     solve_and_save(f, cp_dir + "_1800s", 1800)

# ************* Main Program ************************


# pathes = [r"D:\Ilyaz\PycharmProjects\Emulators\GeneratedProblemsTest"]
# pathes = [r"D:\Ilyaz\PycharmProjects\Emulators\Problem Sets\NewSet"]
# pathes = ["C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\NewSet"]
# pathes = [r"D:\Ilyaz\PycharmProjects\Emulators\Problem Sets\BigProblems\GeneratedProblems_Big"]
# pathes = [r"D:\Ilyaz\PycharmProjects\Emulators\Problem Sets\NewSet\DualObjective"]
pathes = [r"D:\Ilyaz\PycharmProjects\Emulators\Problem Sets\NewSet\DualObjective"]

for p in pathes:
    solve_path(p)


