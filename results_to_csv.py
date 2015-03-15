import os
import sys

if len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    #Raw_input is used to collect data from the user
    base_path = raw_input('> ')    
else:
    base_path = sys.argv[0]

if os.path.isdir(base_path) == False:
    print base_path + ", is not a directory, exit or enter directory name"
    base_path = raw_input('> ')


#dir_list = ["RPFGuan_Penalty_bounded","Layout_Penalty_bounded","TBased_Penalty_bounded","RPFGuan_Penalty","Layout_Penalty","TBased_Penalty", "CP_Penalty_lower"]
#col_perfix = ["guan_penalty_bounded","heragu_penalty_bounded","our_penalty_bounded","guan_penalty","heragu_penalty","our_penalty","cp_penalty_lower"]
#dir_list = ["RPFGuan_Penalty","RPFGuan_Penalty_Bounded","TBased_Penalty","TBased_Penalty_Bounded"]
#dir_list = ["TBased_Div2.0","TBased_Div3.0","TBased_Div5.0","TBased_Div10.0"]
#dir_list = ["TBasedW_Penalty_2.0","TBasedW_Penalty_3.0","TBasedW_Penalty_5.0","TBasedW_Penalty_10.0"]
#dir_list = ["RPFGuan_Penalty_10sec","RPFGuan_Penalty_20sec","RPFGuan_Penalty_30sec"]
#dir_list = ["RPFGuan_Penalty","TBasedW_Penalty"]
dir_list = ["CP_Penalty"]
col_prefix2 = [x.lower()+y for x in dir_list for y in ["_solution","_optimal","_time"]]

files = set()
for d in dir_list:
    path = os.path.join(base_path,d)
    files = files.union(set([x for x in os.listdir(path) if os.path.splitext(x)[1] == ".out"])) # and os.path.splitext(x)[0].endswith("f7.csv")]))



#rpfguan_results_path= os.path.join(base_path,"RPFGuan_Penalty_bounded")
#layout_results_path = os.path.join(base_path,"Layout_Penalty_bounded")
#tbased_results_path = os.path.join(base_path,"TBased_Penalty_bounded")

path_out = os.path.join(base_path,"results_cp_limits.csv")

#first_line = "file,guan_solution,guan_optimal,guan_time,heragu_solution,heragu_optimal,heragu_time,our_solution,our_optimal,our_time"
first_line = ",".join(["file"] + col_prefix2)


#rf_rpfguan = set([x for x in os.listdir(rpfguan_results_path) if os.path.splitext(x)[1] == ".out"])
#rf_layout = set([x for x in os.listdir(layout_results_path) if os.path.splitext(x)[1] == ".out"])
#rf_tbased = set([x for x in os.listdir(tbased_results_path) if os.path.splitext(x)[1] == ".out"])

#files = rf_rpfguan.union(rf_layout).union(rf_tbased)


lines = [first_line]

files = sorted(files)

for f in files:
    ffline = [f]
    for dir in dir_list:
        ff = os.path.join(base_path,dir,f)
        if os.path.exists(ff):
            ez = open(ff)
            tmpline = ez.readline().replace("\n","")
            if tmpline.split(",")[0] == "-1":
                ffline.append("NA,NA," + tmpline.split(",")[2])
            else: 
                ffline.append(tmpline)
        else:
            ffline.append("NA,NA,NA")
    lines.append(",".join(ffline))

ftmp = open(path_out,"w")
ftmp.writelines('\n'.join(lines))
ftmp.close()
