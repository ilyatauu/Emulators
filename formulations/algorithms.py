def get_edr_single_machine_max_time(jobs_info):
    max_time = 0
    for j in jobs_info:
        max_time += j.processtime + j.readytime

    return max_time
