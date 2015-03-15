import sys
import os
import common
import RPFGuan
import TBased
import csv


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

lbfile = os.path.join(path, "lower_bound.out")
ubfile = os.path.join(path, "upper_bound.out")

if os.path.exists(os.path.join(path, lbfile)):
    with open(lbfile, 'rb') as csvfile:
        lbdata = list(csv.reader(csvfile, delimiter=','))

if os.path.exists(os.path.join(path, ubfile)):
    with open(ubfile, 'rb') as csvfile:
        ubdata = list(csv.reader(csvfile, delimiter=','))

# layout_dir = os.path.join(path,"Layout_Penalty")
rpfguan_dir = os.path.join(path, "RPFGuan_Penalty")
tbased_w_dir = os.path.join(path, "TBasedW_Penalty")
# tbased_dir = os.path.join(path,"TBased_Penalty")

# layout_dir_bounded = os.path.join(path,"Layout_Penalty_Bounded")
# rpfguan_dir_bounded = os.path.join(path,"RPFGuan_Penalty_Bounded")
# tbased_dir_bounded = os.path.join(path,"TBased_Penalty_Bounded")


for f in data_files:
    filename = os.path.basename(f)
    props = common.SolutionProps()

    # if not os.path.exists(os.path.join(layout_dir, filename + ".out")):
    #    common.solve_and_save(f,layout_dir,Layout.solve_cplex_only,props)

    # Guan solution
    if not os.path.exists(os.path.join(rpfguan_dir, filename + ".out")):
        prev_sol = common.get_previous_factored_solution(os.path.join(rpfguan_dir, filename + ".out"))
        # if the solution was not proved to be optimal no point to run something harder
        if prev_sol is not None and int(prev_sol[0][1]) == 0:
            out_file = os.path.join(rpfguan_dir, filename + ".out")
            outf = open(out_file, "w")
            outf.writelines("{},{},{}\n".format(prev_sol[0][0], prev_sol[0][1], prev_sol[0][2]))
            outf.flush()
            outf.close()
        else:
            common.solve_and_save(f, rpfguan_dir, RPFGuan.solve_cplex_only, props)

    # TBasedW
    out_file = os.path.join(tbased_w_dir, filename + ".out")
    if not os.path.exists(out_file):
        file_data = common.load_data2(f)
        cplex_result = TBased.solve_cplex__number_of_tardy_jobs_w(file_data[0], file_data[1])
        if not os.path.exists(tbased_w_dir):
            os.mkdir(tbased_w_dir)
        print common.get_output_string(cplex_result)
        outf = open(out_file, "w")
        outf.writelines(common.get_output_string(cplex_result))
        outf.flush()
        outf.close()

            # if not os.path.exists(os.path.join(tbased_dir, filename + ".out")):
            #    common.solve_and_save(f,tbased_dir,TBased.solve_cplex_only,props)

            # if lbdata != None:
            #    props.total_penalty_lower_bound = int([x[1] for x in lbdata if x[0] == filename][0])

            # if lbdata != None:
            #    props.total_penalty_upper_bound = int([x[1] for x in ubdata if x[0] == filename][0])

            # if not os.path.exists(os.path.join(layout_dir_bounded, filename + ".out")):
            #    common.solve_and_save(f,layout_dir_bounded,Layout.solve_cplex_only,props)
            # if not os.path.exists(os.path.join(rpfguan_dir_bounded, filename + ".out")):
            #    common.solve_and_save(f,rpfguan_dir_bounded,RPFGuan.solve_cplex_only,props)
            # if not os.path.exists(os.path.join(tbased_dir_bounded, filename + ".out")):
            #    common.solve_and_save(f,tbased_dir_bounded,TBased.solve_cplex_only,props)
