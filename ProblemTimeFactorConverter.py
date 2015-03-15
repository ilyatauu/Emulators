import common
import ProblemGenerator
import sys
import os

def file_data_to_problem_data_format(file_data):
    problem_data = []
    problem_data.append([file_data[1]])

    for i in range(0,len(file_data[0])):
        problem_data.append(file_data[0][i])

    return problem_data
    



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

data_files = sorted([os.path.join(path,x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv" and os.path.splitext(x)[0].endswith("f1")])

for f in data_files:
    filename = os.path.basename(f)
    file_data = common.load_data2(f)
    problem_data = file_data_to_problem_data_format(file_data)
    factored_problem = ProblemGenerator.multiply_time_units(problem_data,7)
    f_filename = f.replace("f1","f7")
    ProblemGenerator.save_problem_to_file(factored_problem,f_filename)