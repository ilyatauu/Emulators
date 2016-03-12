import csv
from formulations import structures

def load_data(filename):
    emulators_data = structures.EmulatorsData()
    if filename is not None:
        # read csv file
        with open(filename, 'rb') as csvfile:
            lines = list(csv.reader(csvfile, delimiter=','))

        emulators_data.boards_number = int(lines[0][0])
        for i in range(1, len(lines)):
            jinfo = structures.JobInfo()
            jinfo.job_id = int(lines[i][0])
            jinfo.processtime = int(lines[i][1])
            jinfo.duedate = int(lines[i][2])
            jinfo.size = int(lines[i][3])
            jinfo.readytime = int(lines[i][4])
            emulators_data.jobs_info.append(jinfo)

    return emulators_data

def serialize_as_strings(schedule_result):
    """ Create csv string output in format
        the first line will contain:
        objective_value,is_optimal,total_solve_time
        isoptimal will equal 1 if solution is optimal or proved that there is no solution 0 otherwise

        All other lines will contain the data in format:
        jobid, starttime, first_board, tardiness
1
        if there is no solution, only one line with value -1 for the objective value will be
    """

    if schedule_result.optimal:
        optimal_int = 1
    else:
        optimal_int = 0

    if not schedule_result.feasible:
        return "-1," + repr(optimal_int) + "," + repr(schedule_result.total_solve_time)

    output = ["{},{},{},{},{}".format(repr(schedule_result.objective_value),
                                      repr(optimal_int),
                                      repr(schedule_result.total_solve_time),
                                      repr(schedule_result.relative_gap),
                                      repr(schedule_result.model_build_time),
                                      repr(schedule_result.model_solution_time))
              ] + [
        "{0},{1},{2},{3}".format(i.job_id, i.start_time, i.first_board, i.tardiness) for i in schedule_result.jobs_info]
    return '\n'.join(output)
