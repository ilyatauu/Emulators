import sys
import os
import common
import Layout
import RPFGuan
import TBased
import csv
import cpbased


def solve_and_save(fullfilename, cp_dir, seconds_limit):
    filename = os.path.basename(f)
    file_out = os.path.join(cp_dir,filename + "_limit" + `seconds_limit` + "s.out")
    
    if os.path.exists(file_out):
        return

    problem_data = common.load_data2(fullfilename)
    solver = cpbased.EmulatorsCpSolver()
    solver.total_penalty_lower_bound = None
    solver.time_limit = seconds_limit
    result = solver.solve_penalty_only(problem_data[0],problem_data[1])
    print "Objective value: " + `result.objective_value`

    file_out = os.path.join(cp_dir,filename + "_limit" + `seconds_limit` + "s.out")
    outf = open(file_out,"w")

    if result.optimal == True:
        optimal_int = 1
    else:
        optimal_int = 0

    if result.feasible == False:
        output = ["-1," + `optimal_int`] + ["\n"]
    else:
        output = [`result.objective_value` + ","+ `optimal_int` + "," + `result.total_run_time`] + ["\n"]
    
    outf.writelines(output)
    outf.flush()
    outf.close()



#************* Main Program ************************
if len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    #Raw_input is used to collect data from the user
    path = raw_input('> ')    
else:
    path = sys.argv[0]

if os.path.isdir(path) == False:
    print path + ", is not a directory, exit or enter directory name"
    path = raw_input('> ')

data_files = sorted([os.path.join(path,x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv"])

lbfile = os.path.join(path,"lower_bound.out")
ubfile = os.path.join(path,"upper_bound.out")

lbdata = None
if os.path.exists(os.path.join(path, lbfile)):
    with open(lbfile, 'rb') as csvfile:
        lbdata = list(csv.reader(csvfile, delimiter=','))

cp_dir = os.path.join(path,"CP_Penalty")

if not os.path.exists(cp_dir):
    os.mkdir(cp_dir)

for f in data_files:
    filename = os.path.basename(f)
    
    solve_and_save(f,cp_dir,1)
    solve_and_save(f,cp_dir,2)
    solve_and_save(f,cp_dir,3)
        
    #if os.path.exists(os.path.join(cp_dir,filename + ".out")):
    #    continue
    
    ##returns data from the file as a matrix (int format)
    #data = common.load_data2(f);
    ##data related to jobs is starting from the second row in the matrix
    #jobs_data = data[0]

    #solver = cpbased.EmulatorsCpSolver()
    #if lbdata != None:
    #    solver.total_penalty_lower_bound = int([x[1] for x in lbdata if x[0] == filename][0])
    #else:
    #    solver.total_penalty_lower_bound = None
    #solver.time_limit = 1
    #result = solver.solve_penalty_only(jobs_data,data[1])
    #print "Objective value: " + `result.objective_value`

    #if not os.path.exists(cp_dir):
    #    os.mkdir(cp_dir)

    #file_out = os.path.join(cp_dir,filename + ".out")
    #outf = open(file_out,"w")

    #if result.optimal == True:
    #    optimal_int = 1
    #else:
    #    optimal_int = 0

    #if result.feasible == False:
    #    output = ["-1," + `optimal_int`] + ["\n"]
    #else:
    #    output = [`result.objective_value` + ","+ `optimal_int` + "," + `result.total_run_time`] + ["\n"]
    
    #outf.writelines(output)
    #outf.close()


