import re
import os

class StatsResult(object):
    def __init__(self):
        self.solution_value = -1
        self.optimal = -1


def load_schedule_result(result_file):
    ez = open(result_file)
    tmpline = ez.readline().replace("\n", "")
    arr = tmpline.split(",")
    r = StatsResult()
    if arr[0] == "-1":
        return r
    else:
        r.solution_value = int(arr[0])
        r.optimal = int(arr[1])
    return r

def get_path_files(path):
    files = set()
    files = files.union(set([os.path.join(path, x) for x in os.listdir(path) if os.path.splitext(x)[1] == ".out"]))
    return files

def load_results(path):
    files = get_path_files(path)
    results = [load_schedule_result(x) for x in files]
    return results

def parse_problem_params(filename):
    # example: m15j15d15p05_0
    pattern = "m(?P<machines>[0-9]+)j(?P<jobs>[0-9]+)" \
              "d(?P<duedate>[0-9]+)p(?P<processtime>[0-9]+)_(?P<iteration>[0-9]+).*"

    match = re.search(pattern, filename)
    m = match.group("machines")
    j = match.group("jobs")
    d = match.group("duedate")
    p = match.group("processtime")
    i = match.group("iteration")

    return m, j, d, p, i

def get_results_permutations(path):
    permutations = set(["m{}j{}d{}p{}".format(y[0], y[1], y[2], y[3])
                        for y in  [parse_problem_params(x) for x in get_path_files(path)]])
    # print permutations
    # print len(permutations)

    return permutations

def permutation_files(path, permutation):
    return [x for x in get_path_files(path) if permutation in x]

def get_average(results):
    values = [x.solution_value for x in results]
    return float(sum(values))/max(len(values), 1)


path = r"D:\Ilyaz\PycharmProjects\Emulators\GeneratedProblemsTest\tbasedu"
pf = [(permutation_files(path, x), x) for x in get_results_permutations(path)]

results = [ (map(load_schedule_result,y[0]),y[1])
            for y in [(permutation_files(path, x), x) for x in get_results_permutations(path)]]
avg = [(get_average(x[0]), x[1]) for x in results]

avg = sorted(avg, key=lambda x: x[1])
print len(avg)
print avg

# average = get_average(load_results(path))
# print (average)


