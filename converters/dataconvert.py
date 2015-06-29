import math
from formulations import structures

def divide_time_feasible(emulators_data, divider):
    divider = float(divider)
    new_data = structures.EmulatorsData()
    new_data.boards_number = emulators_data.boards_number

    for j in emulators_data.jobs_info:
        new_job_info = structures.JobInfo()
        new_job_info.job_id = j.job_id
        new_job_info.processtime = max(1, int(math.ceil(j.processtime / divider)))
        new_job_info.duedate = max(new_job_info.processtime, int(math.floor(j.duedate / divider)))
        new_job_info.size = j.size
        new_job_info.readytime = max(0, int(math.ceil(j.readytime / divider)))

        new_data.jobs_info.append(new_job_info)

    return new_data

def divide_time_optimistic(emulators_data, divider):
    divider = float(divider)
    new_data = structures.EmulatorsData()
    new_data.boards_number = emulators_data.boards_number

    for j in emulators_data.jobs_info:
        new_job_info = structures.JobInfo()
        new_job_info.job_id = j.job_id
        new_job_info.processtime = max(1, int(math.floor(j.processtime / divider)))
        new_job_info.duedate = max(new_job_info.processtime, int(math.ceil(j.duedate / divider)))
        new_job_info.size = j.size
        new_job_info.readytime = max(0, int(math.floor(j.readytime / divider)))

        new_data.jobs_info.append(new_job_info)

    return new_data



