import sys
import os
import common


def get_outfilename(problem_file, dirname):
    basepath, filename = os.path.split(problem_file)
    return os.path.join(basepath, dirname, filename + ".out")

def solve_combined(r, problem_file):
    out_file = get_outfilename(problem_file, "cfp" + repr(r))
    if not os.path.exists(out_file):
        common.solve_and_save_guantbased_combined_feasible(problem_file, out_file, float(r))

    out_file = get_outfilename(problem_file, "cnfp" + repr(r))
    if not os.path.exists(out_file):
        common.solve_and_save_guantbased_combined_optimistic(problem_file, out_file, float(r))

    out_file = get_outfilename(problem_file, "crnd" + repr(r))
    if not os.path.exists(out_file):
        common.solve_and_save_guantbased_combined_round(problem_file, out_file, float(r))


def solve_guan(problem_file, timelimit):
    out_file = get_outfilename(problem_file, "guan_{}s".format(timelimit))
    if not os.path.exists(out_file):
        common.solve_and_save2(problem_file, out_file, "guan", "tardy_jobs", timelimit=timelimit)

def solve_tbased(problem_file, timelimit):
    out_file = get_outfilename(problem_file, "tbased_{}s".format(timelimit))
    if not os.path.exists(out_file):
        common.solve_and_save2(problem_file, out_file, "tbased", "tardy_jobs", timelimit=timelimit)

def get_histogram(values):
    h = dict()
    for v in values:
        h[v] = h.get(v, 0)+1

    return h

def solve_path(path):
    data_files = sorted([os.path.join(path, x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv"])
    for f in data_files:
        filename = os.path.basename(f)
        if filename.startswith("results") or "p60" in filename:
            continue

        print f

        solve_guan(f, 1)
        solve_guan(f, 2)
        solve_guan(f, 5)
        solve_guan(f, 10)
        solve_guan(f, 20)
        solve_guan(f, 50)
        solve_guan(f, 100)
        solve_guan(f, 200)
        solve_guan(f, 400)
        solve_guan(f, 800)
        solve_guan(f, 1200)

        # solve_tbased(f, 1)
        # solve_tbased(f, 2)
        # solve_tbased(f, 5)
        # solve_tbased(f, 10)
        # solve_tbased(f, 20)
        # solve_tbased(f, 50)
        # solve_tbased(f, 100)
        # solve_tbased(f, 200)
        # solve_tbased(f, 400)
        # solve_tbased(f, 800)
        # solve_tbased(f, 1200)

        # solve_combined(80, f)
        # solve_combined(40, f)
        # solve_combined(20, f)
        # solve_combined(10, f)
        # solve_combined(5, f)
        # solve_combined(3, f)

def get_path_from_user():
    if len(sys.argv) < 2:
        print 'Please enter directory with problems data'
        # Raw_input is used to collect data from the user
        userpath = raw_input('> ')
    else:
        userpath = sys.argv[1]

    if not os.path.isdir(userpath):
        print userpath + ", is not a directory, exit or enter directory name"
        userpath = raw_input('> ')

    return userpath

# ************* Main Program ************************
# path = None
# path = "C:\Users\izaides\PycharmProjects\Emulators\GeneratedProblems_201504152238"
# path = "C:\Users\izaides\PycharmProjects\Emulators\TestIntegrability"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium\ProblemsWithP60_80"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problems_P80_MSize5"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\BigProblems\GeneratedProblems_Big"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium"


solve_path(r"D:\Ilyaz\PycharmProjects\Emulators\Problem Sets\BigProblems\GeneratedProblems_Big\ProblemsToAnalyzeRate")