import os
import sys
import re


def parse_problem_filename(filename):
    # example: m15j15d15p05_0
    pattern = "m(?P<machines>[0-9]+)j(?P<jobs>[0-9]+)" \
              "d(?P<duedate>[0-9]+)p(?P<processtime>[0-9]+)_(?P<iteration>[0-9]+).*"

    match = re.search(pattern, filename)
    m = match.group("machines")
    j = match.group("jobs")
    d = match.group("duedate")
    p = match.group("processtime")
    i = match.group("iteration")

    return [m, j, d, p, i]

def parse_out_filename(filename):
    # example: m15j30d20p05_0.csv_limit1s.out
    pattern = "m(?P<machines>[0-9]+)j(?P<jobs>[0-9]+)" \
              "d(?P<duedate>[0-9]+)p(?P<processtime>[0-9]+)_(?P<iteration>[0-9]+).*_limit(?P<seclimit>[0-9])?.*"

    match = re.search(pattern, filename)
    m = match.group("machines")
    j = match.group("jobs")
    d = match.group("duedate")
    p = match.group("processtime")
    i = match.group("iteration")
    l = match.group("seclimit")

    if l is None:
        l = 1800

    return [m, j, d, p, i, l]

if len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    # Raw_input is used to collect data from the user
    base_path = raw_input('> ')    
else:
    base_path = sys.argv[0]

if os.path.isdir(base_path) is False:
    print base_path + ", is not a directory, exit or enter directory name"
    base_path = raw_input('> ')


# dir_list = ["RPFGuan_Penalty_bounded","Layout_Penalty_bounded","TBased_Penalty_bounded",
#   "RPFGuan_Penalty","Layout_Penalty","TBased_Penalty", "CP_Penalty_lower"]
# col_perfix = ["guan_penalty_bounded","heragu_penalty_bounded","our_penalty_bounded","guan_penalty",
#   "heragu_penalty","our_penalty","cp_penalty_lower"]
# dir_list = ["RPFGuan_Penalty","RPFGuan_Penalty_Bounded","TBased_Penalty","TBased_Penalty_Bounded"]
# dir_list = ["TBased_Div2.0","TBased_Div3.0","TBased_Div5.0","TBased_Div10.0"]
# dir_list = ["TBasedW_Penalty_2.0","TBasedW_Penalty_3.0","TBasedW_Penalty_5.0","TBasedW_Penalty_10.0"]
# dir_list = ["RPFGuan_Penalty_10sec","RPFGuan_Penalty_20sec","RPFGuan_Penalty_30sec"]
# dir_list = ["RPFGuan_Penalty","TBasedW_Penalty"]
# dir_list = ["CP_Penalty"]
# dir_list = ["guan", "tbasedw", "combined"]
# dir_list = ["cfp10_1", "cnfp10_1"]
# dir_list = ["cfp5_1"]
dir_list = ["cfp10", "cfp8", "cfp5", "cfp3"]
# dir_list = ["CP_1s", "CP_2s", "CP_5s", "CP_10s", "CP_20s"]
# dir_list = ["Guan", "TBased2", "CP_limit1s", "CP_limit2s", "CP_limit5s", "CP_limit10s", "CP_limit20s"]
# This columns are for Guan and TBased formulations
col_prefix2 = []


for dd in dir_list:
    if dd.startswith("CP"):
        col_prefix2 = col_prefix2 + [dd.lower() + x
                                     for x in ["_solution", "_optimal", "_time"]]
    else:
        col_prefix2 = col_prefix2 + [dd.lower() + x
                                     for x in ["_solution", "_optimal", "_time", "_gap", "_build_time",
                                               "_model_time", "_solution_time"]]

files = set()
for dd in dir_list:
    path = os.path.join(base_path, dd)
    files = files.union(set([x for x in os.listdir(path) if os.path.splitext(x)[1] == ".out"]))
    # and os.path.splitext(x)[0].endswith("f7.csv")]))

# rpfguan_results_path= os.path.join(base_path,"RPFGuan_Penalty_bounded")
# layout_results_path = os.path.join(base_path,"Layout_Penalty_bounded")
# tbased_results_path = os.path.join(base_path,"TBased_Penalty_bounded")

path_out = os.path.join(base_path, "results.csv")

# first_line = "file,guan_solution,guan_optimal,guan_time,heragu_solution,
# heragu_optimal,heragu_time,our_solution,our_optimal,our_time"
first_line = ",".join(["file", "m", "j", "d", "p", "i"] + col_prefix2)


# rf_rpfguan = set([x for x in os.listdir(rpfguan_results_path) if os.path.splitext(x)[1] == ".out"])
# rf_layout = set([x for x in os.listdir(layout_results_path) if os.path.splitext(x)[1] == ".out"])
# rf_tbased = set([x for x in os.listdir(tbased_results_path) if os.path.splitext(x)[1] == ".out"])

# files = rf_rpfguan.union(rf_layout).union(rf_tbased)


lines = [first_line]

files = sorted(files)

for f in files:
    ffline = [f]
    params = parse_problem_filename(f)
    ffline = ffline + params
    for d in dir_list:
        ff = os.path.join(base_path, d, f)
        if os.path.exists(ff):
            ez = open(ff)
            tmpline = ez.readline().replace("\n", "")
            if tmpline.split(",")[0] == "-1":
                ffline.append("NA,NA," + tmpline.split(",")[2])
            elif len(tmpline.split(",")) == 3:
                ffline.append(tmpline)
            else:
                tmparr = tmpline.split(',')
                if len(tmparr) == 5:
                    ffline.append(tmpline + ',' + ',' + str(float(tmparr[2])-float(tmparr[4])))
                else:
                    ffline.append(tmpline + ',' + str(float(tmparr[2])-float(tmparr[4])))
        else:
            ffline.append("NA,NA,NA")
    lines.append(",".join(ffline))

ftmp = open(path_out, "w")
ftmp.writelines('\n'.join(lines))
ftmp.close()
