import csv
import sys
import os
import copy
import formulations.cplex_mip
import formulations.structures
import converters.fileconvert
import converters.dataconvert




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

def get_builder_and_reader(formulation_type, problem_type):
    def get_key(phase):
        return "{}_{}_{}".format(formulation_type, problem_type, phase)
    if not hasattr(get_builder_and_reader, "fmap"):
        get_builder_and_reader.fmap = {}
    fmap = get_builder_and_reader.fmap

    if get_key("builder") not in fmap:
        fmap[get_key("builder")] = formulations.cplex_mip.get_formulation_builder(
            formulation_type, problem_type)
    if get_key("reader") not in fmap:
        fmap[get_key("reader")] = formulations.cplex_mip.get_results_reader(formulation_type)

    return fmap[get_key("builder")], fmap[get_key("reader")]

def solve_and_save2(filename, outputfilename, formulation_type, problem_type):

    builder, reader = get_builder_and_reader(formulation_type, problem_type)
    data = converters.fileconvert.load_data(filename)
    schedule = formulations.cplex_mip.solve(data, builder, reader)

    write_schedule(schedule, outputfilename)

def solve_and_save_withdivide(filename, outputfilename, formulation_type, problem_type, divider):
    builder, reader = get_builder_and_reader(formulation_type, problem_type)
    data = converters.fileconvert.load_data(filename)
    new_data = converters.dataconvert.divide_time_feasible(data, float(divider))
    schedule1 = formulations.cplex_mip.solve(new_data, builder, reader)
    write_schedule(schedule1, outputfilename)

def solve_and_save_guantbased_combined(filename, outputfilename, divider, dataconverter):

    builder, reader = get_builder_and_reader("tbasedw", "tardy_jobs")
    data = converters.fileconvert.load_data(filename)
    new_data = dataconverter(data, float(divider))
    schedule_t = formulations.cplex_mip.solve(new_data, builder, reader)

    # write_schedule(schedule_t, outputfilename + ".tbasedw")
    order = get_solution_order(schedule_t)

    builder, reader = get_builder_and_reader("guan", "tardy_jobs")

    def add_order_constraint(formulation_model):
        import formulations.guan.tardyjobs
        formulations.guan.tardyjobs.add_decision_vars_constraints(formulation_model, order)

    schedule_g = formulations.cplex_mip.solve(data, builder, reader, [add_order_constraint])

    joined_schedule = join_schedules(schedule_t, schedule_g)

    write_schedule(schedule_g, outputfilename + ".guan")
    write_schedule(schedule_t, outputfilename + ".tbased")

    write_schedule(joined_schedule, outputfilename)


def solve_and_save_guantbased_combined_feasible(filename, outputfilename, divider):
    solve_and_save_guantbased_combined(filename, outputfilename,
                                       divider, converters.dataconvert.divide_time_feasible)


def solve_and_save_guantbased_combined_optimistic(filename, outputfilename, divider):
    solve_and_save_guantbased_combined(filename, outputfilename,
                                       divider, converters.dataconvert.divide_time_optimistic)

def solve_and_save_guantbased_combined_round(filename, outputfilename, divider):
    solve_and_save_guantbased_combined(filename, outputfilename,
                                       divider, converters.dataconvert.divide_time_rounding)


def write_schedule(schedule, fullfilename):
    serialized = converters.fileconvert.serialize_as_strings(schedule)
    outputdir = os.path.dirname(fullfilename)
    # write results to file
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)

    outf = open(fullfilename, "w")
    outf.writelines(serialized)
    outf.close()

def get_solution_order(schedule):
    """
    :param schedule: a solution schedule
    :return: list of tuples (delta_ij, sigma_ij)
        delta_ij - whether i is starting before job j
        sigma_ij - whether i is starting before jobs j
        if the condition is true for both of the options only one will be chosen
        the rule is the one with biggest difference is chosen
    """
    def get_id(x):
        return repr(x.job_id)

    def get_last_cmpletion_time():
        return max(schedule.jobs_info, key=lambda x: x.finish_time)

    time_horizon = float(get_last_cmpletion_time())
    boards_number = schedule.boards_number
    big_number = 2 * time_horizon + boards_number

    def get_time_proportion(j1, j2):
        return (j1.finish_time - j2.start_time) * big_number / time_horizon

    def get_size_proportion(j1, j2):
        return (j1.finish_board - j2.first_board) * big_number / boards_number

    pdcit = dict()
    for j in schedule.jobs_info:
        for i in schedule.jobs_info:
            if j.job_id == i.job_id:
                continue

            tmp_value = min([(get_time_proportion(j, i), (1, 0)),
                             (get_size_proportion(j, i), (0, 1)),
                             (0.01, (0, 0))
                             ], key=lambda x: x[0])

            if tmp_value[0] <= 0:
                pdcit[get_id(j) + ',' + get_id(i)] = tmp_value[1]

    return pdcit

def join_schedules(schedule1, schedule2):
    joined = formulations.structures.ScheduleResult()
    joined.feasible = schedule1.feasible & schedule2.feasible
    joined.optimal = schedule1.optimal & schedule2.optimal
    joined.objective_value = schedule2.objective_value
    joined.total_penalty = schedule2.total_penalty
    joined.total_tardiness = schedule2.total_tardiness
    joined.jobs_info = schedule2.jobs_info
    joined.total_solve_time = schedule1.total_solve_time + schedule2.total_solve_time
    joined.relative_gap = schedule1.relative_gap + schedule2.relative_gap
    joined.model_build_time = schedule1.model_build_time + schedule2.model_build_time
    joined.model_solution_time = schedule1.model_solution_time + schedule2.model_solution_time

    return joined

