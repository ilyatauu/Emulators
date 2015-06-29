import sys
import os
import common



# ************* Main Program ************************
path = None
# path = "C:\Users\izaides\PycharmProjects\Emulators\GeneratedProblems_201504152238"
# path = "C:\Users\izaides\PycharmProjects\Emulators\TestIntegrability"
path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium\ProblemsWithP60_80"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\BigProblems\GeneratedProblems_Big"
# path = "C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium"
if path is None and len(sys.argv) < 2:
    print 'Please enter directory with problems data'
    # Raw_input is used to collect data from the user
    path = raw_input('> ')
elif path is None:
    path = sys.argv[1]

if os.path.isdir(path) is False:
    print path + ", is not a directory, exit or enter directory name"
    path = raw_input('> ')

data_files = sorted([os.path.join(path, x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".csv"])

for f in data_files:
    filename = os.path.basename(f)
    if filename.startswith("results"):
        continue

    if "p60" in filename:
        continue

    print filename

    # if not os.path.exists(os.path.join(path, "guan", filename + ".out")):
    #     common.solve_and_save2(f, os.path.join(path, "guan"), "guan", "tardy_jobs")

    if not os.path.exists(os.path.join(path, "cfp10_1", filename + ".out")):
        common.solve_and_save_guantbased_combined_feasible(f, os.path.join(path, "cfp10_1",
                                                                           filename + ".out"), 10.0)

    if not os.path.exists(os.path.join(path, "cnfp10_1", filename + ".out")):
        common.solve_and_save_guantbased_combined_optimistic(f, os.path.join(path, "cnfp10_1",
                                                                             filename + ".out"), 10.0)

    # if not os.path.exists(os.path.join(path, "cfp5", filename + ".out")):
    #     common.solve_and_save_guantbased_combined_feasible(f, os.path.join(path, "cfp5",
    #                                                                        filename + ".out"), 5.0)
    #
    # if not os.path.exists(os.path.join(path, "cnfp5", filename + ".out")):
    #     common.solve_and_save_guantbased_combined_optimistic(f, os.path.join(path, "cnfp5",
    #                                                                          filename + ".out"), 5.0)

    # if not os.path.exists(os.path.join(path, "tbasedw", filename + ".out")):
    #     common.solve_and_save2(f, os.path.join(path, "tbasedw", filename + ".out"), "tbasedw", "tardy_jobs")
