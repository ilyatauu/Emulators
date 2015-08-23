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

        out_file = get_outfilename(f, "guan")
        if not os.path.exists(out_file):
            common.solve_and_save2(f, out_file, "guan", "tardy_jobs")

        out_file = get_outfilename(f, "tbased")
        if not os.path.exists(out_file):
            common.solve_and_save2(f, out_file, "tbasedw", "tardy_jobs")

        solve_combined(80, f)
        solve_combined(40, f)
        solve_combined(20, f)
        solve_combined(10, f)
        solve_combined(5, f)
        solve_combined(3, f)

def get_path_from_user():
    if len(sys.argv) < 2:
        print 'Please enter directory with problems data'
        # Raw_input is used to collect data from the user
        userpath = raw_input('> ')
    else:
        userpath = sys.argv[1]

    if not os.path.isdir(userpath):
        print userpath + ", is not a directory, exit or enter directory name"
        path = raw_input('> ')

    return userpath

# ************* Main Program ************************
path = None
# path = "C:\Users\izaides\PycharmProjects\Emulators\GeneratedProblems_201504152238"
# path = "C:\Users\izaides\PycharmProjects\Emulators\TestIntegrability"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium\ProblemsWithP60_80"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problems_P80_MSize5"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\BigProblems\GeneratedProblems_Big"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium"


solve_path(r"C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\MediumBigDuedate")