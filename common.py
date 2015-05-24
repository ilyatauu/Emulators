import csv
import sys
import os
import copy


class CplexResult(object):
    feasible = None
    optimal = None
    objective_value = None
    total_penalty = None
    total_tardiness = None
    job_info = []
    total_solve_time = None
    relative_gap = None
    model_build_time = None
    model_solution_time = None


class JobInfo(object):
    job_id = None
    start_time = None
    finish_time = None
    first_board = None
    finish_board = None
    tardiness = None


class SolutionProps:

    def __init__(self):
        pass

    total_penalty_lower_bound = None
    total_penalty_upper_bound = None


def load_data2(filename):
    data = None
    if filename is not None:
        # read csv file
        with open(filename, 'rb') as csvfile:
            data = list(csv.reader(csvfile, delimiter=','))
            # convert to int
            for row in data:
                for i in range(len(row)):
                    if row[i] is not '':
                        row[i] = int(row[i])

    # data related to jobs is starting from the second row in the matrix
    jobs_data = []
    for i in range(1, len(data)):
        jobs_data.append(data[i])

    return jobs_data, data[0][0]


def load_solution(filename):
    if filename is None:
        return

    with open(filename, 'rb') as csvfile:
        data = list(csv.reader(csvfile, delimiter=','))

    return data


def get_output_string(cplex_result):
    """ Create csv string output in format
        the first line will contain: 
        objective_value,is_optimal,total_solve_time
        isoptimal will equal 1 if solution is optimal or proved that there is no solution 0 otherwise

        All other lines will contain the data in format:
        jobid, starttime, first_board, tardiness

        if there is no solution, only one line with value -1 for the objective value will be
    """

    if cplex_result.optimal:
        optimal_int = 1
    else:
        optimal_int = 0

    if not cplex_result.feasible:
        return "-1," + repr(optimal_int) + "," + repr(cplex_result.total_solve_time)

    output = ["{},{},{},{},{}".format(repr(cplex_result.objective_value),
                                      repr(optimal_int),
                                      repr(cplex_result.total_solve_time),
                                      repr(cplex_result.relative_gap),
                                      repr(cplex_result.model_build_time))
              ] + [
        "{0},{1},{2},{3}".format(i.job_id, i.start_time, i.first_board, i.tardiness) for i in cplex_result.job_info]
    return '\n'.join(output)


def get_edr_single_machine_max_time(jobs_data):
    max_time = 0
    for j in jobs_data:
        max_time += j[1] + j[4]

    return max_time


def moores_single_machine_tardy_jobs_with_slicing(jobs_data, number_of_boards):
    jobs_data_new = copy.deepcopy(jobs_data)

    # modify job process time to be (p_i * s_i) / number_of_boards
    for j in jobs_data_new:
        j[1] = (j[1] * j[3]) / (1.0 * number_of_boards)

    # order jobs by due date
    sorted_jobs_data = sorted(jobs_data_new, key=lambda k: k[2])

    early_jobs_data = []
    tardy_jobs_data = []

    for j in sorted_jobs_data:
        if sum([x[1] for x in early_jobs_data]) + j[1] <= j[2]:
            early_jobs_data.append(j)
        else:
            early_jobs_data.append(j)
            max_process_time = max([x[1] for x in early_jobs_data])
            longest_job = [x for x in early_jobs_data if x[1] == max_process_time][0]
            early_jobs_data.remove(longest_job)
            tardy_jobs_data.append(longest_job)

    return early_jobs_data, tardy_jobs_data


def solve_and_save(filename, outputdir, solve_callback, props):
    if filename is None and len(sys.argv) < 2:
        print 'Please enter the full name of the desired file (with extension) at the prompt below'
        # Raw_input is used to collect data from the user
        filename = raw_input('> ')
    elif filename is None:
        filename = sys.argv[1]

    # returns data from the file as a matrix (int format)
    data = load_data2(filename)

    # data related to jobs is starting from the second row in the matrix
    jobs_data = data[0]

    cplex_result = solve_callback(jobs_data, data[1], props)

    print "total solve time: " + repr(cplex_result.total_solve_time)
    print "Objective value: " + repr(cplex_result.objective_value)
    print get_output_string(cplex_result)

    # write results to file
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)

    filename = os.path.basename(filename)
    file_out = os.path.join(outputdir, filename + ".out")
    outf = open(file_out, "w")
    outf.writelines(get_output_string(cplex_result))
    outf.close()


def get_previous_factored_solution(filename):
    if filename is None:
        return None

    factor_index = filename.find("_f")

    if factor_index == -1:
        return None

    factor = int(filename[factor_index + 2:factor_index + 2 + 1])
    previous_filename = filename.replace("f" + repr(factor), "f" + repr(factor - 1))
    if not os.path.exists(previous_filename):
        return None

    previous_solution = load_solution(previous_filename)

    return previous_solution
