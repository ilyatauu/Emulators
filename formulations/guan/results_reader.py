from formulations import structures
from formulations import cplex_mip

def read(model, emulators_data):
    schedule_result = structures.ScheduleResult()
    schedule_result.feasible, schedule_result.optimal = cplex_mip.get_feasibility_and_optimality(model.cplex_class)

    schedule_result.boards_number = emulators_data.boards_number

    jobs_info = []

    for j in emulators_data.jobs_info:
        info = structures.ScheduledJobInfo()
        info.job_id = j.job_id
        info.start_time = int(round(model.cplex_class.solution.get_values(model.vars_map['u' + repr(j.job_id)])))
        info.first_board = int(round(model.cplex_class.solution.get_values(model.vars_map['v' + repr(j.job_id)])))
        info.finish_time = info.start_time + j.processtime
        info.tardiness = max(info.finish_time - j.duedate, 0)
        jobs_info.append(info)

    schedule_result.total_penalty = int(round(sum([model.cplex_class.solution.get_values('U' + repr(j.job_id))
                                                   for j in emulators_data.jobs_info])))
    schedule_result.objective_value = int(round(model.cplex_class.solution.get_objective_value()))
    schedule_result.jobs_info = jobs_info
    schedule_result.relative_gap = model.cplex_class.solution.MIP.get_mip_relative_gap()
    schedule_result.model_build_time = model.model_build_time
    schedule_result.model_solution_time = model.solve_time

    return schedule_result

