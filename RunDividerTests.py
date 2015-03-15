import sys
import os
import common
import Layout
import RPFGuan
import TBased
import csv


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

dividers = [10.0,5.0,3.0,2.0]

#for f in data_files:
#    filename = os.path.basename(f)
#    for div in dividers:
#        div_path = os.path.join(path,"TBased_Div" + `div`)
#        out_file = os.path.join(div_path, filename + ".out")
#        if not os.path.exists(out_file):
#            file_data = common.load_data2(f)
#            cplex_result = TBased.solve_cplex__number_of_tardy_jobs_timedivider(file_data[0], file_data[1],div)
#            if not os.path.exists(div_path):
#                os.mkdir(div_path)
#            print common.get_output_string(cplex_result)
#            outf = open(out_file,"w")
#            outf.writelines(common.get_output_string(cplex_result))
#            outf.close()

dividers = [10.0,5.0,3.0,2.0]
for f in data_files:
    filename = os.path.basename(f)
    if filename != 'm15j15d15_3.csv': continue
    for div in dividers:
        div_path = os.path.join(path,"TBasedW_Penalty_" + `div`)
        out_file = os.path.join(div_path, filename + ".out")
        if not os.path.exists(out_file) or 1==1:
            file_data = common.load_data2(f)
            jobs_data = TBased.get_time_divided_jobs_data(file_data[0],div)
            lines = ["{},{},{},{},{}\n".format(x[0],x[1],x[2],x[3],x[4])  for x in jobs_data]
            dat_file = os.path.join(path, filename + `div` + ".dat" )
            df = open(dat_file,"w")
            df.writelines(lines)
            df.close()
            cplex_result = TBased.solve_cplex__number_of_tardy_jobs_w(jobs_data, file_data[1],div)
            if not os.path.exists(div_path):
                os.mkdir(div_path)
            print common.get_output_string(cplex_result)
            #outf = open(out_file,"w")
            #outf.writelines(common.get_output_string(cplex_result))
            #outf.close()