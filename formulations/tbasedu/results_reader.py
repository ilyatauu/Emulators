from formulations import structures
from formulations import cplex_mip

def read(model, emulators_data):
    schedule_result = structures.ScheduleResult()
    schedule_result.feasible, schedule_result.optimal = cplex_mip.get_feasibility_and_optimality(model.cplex_class)

    schedule_result.boards_number = emulators_data.boards_number
    jobs_info = []

    if not schedule_result.feasible:
        schedule_result.jobs_info = jobs_info
        schedule_result.model_build_time = model.model_build_time
        schedule_result.model_solution_time = model.solve_time
        return schedule_result

    total_penalty = 0
    start_time_of_late_job = model.max_time
    for j in emulators_data.jobs_info:
        if model.cplex_class.solution.get_values(
                model.vars_map['U{0}'.format(j.job_id)]) >= 1-1e-06:
            info = structures.ScheduledJobInfo()
            info.job_id = j.job_id
            info.start_time = start_time_of_late_job
            info.finish_time = info.start_time + j.processtime
            info.first_board = 0
            info.finish_time = info.first_board + j.size
            info.tardiness = max(info.finish_time - j.duedate, 0)
            total_penalty += 1
            jobs_info.append(info)
            # allocation of late jobs like for single machine, one after the other,
            # not best variation for the total tardiness comparison
            start_time_of_late_job = info.finish_time

    for j in emulators_data.jobs_info:
        for m in range(emulators_data.boards_number):
            for t in range(model.max_time):
                if model.cplex_class.solution.get_values(
                        model.vars_map['x{0},{1},{2}'.format(j.job_id, m, t)]) >= 1 - 1e-06:
                    info = structures.ScheduledJobInfo()
                    info.job_id = j.job_id
                    info.start_time = int(round(t))
                    info.finish_time = info.start_time + j.processtime
                    info.first_board = m
                    info.finish_board = info.first_board + j.size
                    info.tardiness = max(info.finish_time - j.duedate, 0)
                    if info.finish_time > j.duedate:
                        total_penalty += 1
                    jobs_info.append(info)


    schedule_result.total_penalty = total_penalty
    schedule_result.objective_value = int(round(model.cplex_class.solution.get_objective_value()))
    schedule_result.jobs_info = jobs_info
    schedule_result.relative_gap = model.cplex_class.solution.MIP.get_mip_relative_gap()
    schedule_result.model_build_time = model.model_build_time
    schedule_result.model_solution_time = model.solve_time

    return schedule_result
