import random
import os
import time


# def generate_job(due_date, process_time, arrival_time, job_size):
#         pi = random.randint(1, process_time)
#         si = random.randint(1, job_size)
#         ai = random.randint(0, arrival_time)
#         di = random.randint(ai+pi, due_date+pi)
#
#         return [pi, di, si, ai]

def generate_job(due_date, process_time, arrival_time, job_size):
        pi = random.randint(process_time[0], process_time[1])
        si = random.randint(job_size[0], job_size[1])
        ai = random.randint(arrival_time[0], arrival_time[1])
        di = random.randint(ai+pi, due_date+pi)

        return [pi, di, si, ai]


def generate_problem(machines, jobs, due_date, process_time, arrival_time, job_size):
    problem_input = [[machines]]

    for i in range(0, jobs):
        problem_input.append([i] + generate_job(due_date, process_time, arrival_time, job_size))

    return problem_input


def multiply_time_units(problem_input, factor):

    problem_input_new = [problem_input[0]]

    for i in range(1, len(problem_input)):
        job_data = [problem_input[i][0], problem_input[i][1] * factor,
                    problem_input[i][2] * factor, problem_input[i][3], problem_input[i][4] * factor]
        problem_input_new.append(job_data)

    return problem_input_new


def save_problem_to_file(problem_input, filename):
    output_file = open(filename, 'w')
    output_file.write(repr(problem_input[0][0]) + '\n')

    for i in range(1, len(problem_input)):
        line = ','.join([repr(x) for x in problem_input[i]]) + '\n'
        output_file.write(line)

    output_file.close()


def create_sample_problem(machines, jobs, due_date, process_time, arrival_time, job_size, filename):
    output_file = open(filename, 'w')

    output_file.write(repr(machines) + '\n')
    # prepare values
    for i in range(0, jobs):
        pi = random.randint(1, process_time)
        si = random.randint(1, job_size)
        ai = random.randint(0, arrival_time)
        di = random.randint(ai+pi, due_date+pi)

        line = ','.join([repr(i), repr(pi), repr(di), repr(si), repr(ai)]) + '\n'
        output_file.write(line)

    output_file.close()


# ************* Main Program ************************
if __name__ == "__main__":

    # Generated problems for identical factored problems
    # jobs_options = [10, 15, 20, 25, 30]
    # due_date_options = [2, 4]
    # machines_options = [5, 10, 15]
    # process_time_options = [4]
    # arrival_time_options = [0]

    ## Big problems
    # jobs_options = [30, 40, 50]
    # due_date_options = [20]
    # machines_options = [15, 25]
    # process_time_options = [[1, 5], [2, 10], [4, 20], [8, 40]]
    # arrival_time_options = [[0, 0]]

    # jobs_options = [15,20,25]
    # due_date_options = [15,20,25]
    # machines_options = [15,20,25]
    # process_time_options = [15]
    # arrival_time_options = [0]

    # jobs_options = [4,8]
    # due_date_options = [10,20]
    # machines_options = [4,6]
    #
    jobs_options = [25]
    due_date_options = [15, 25]
    machines_options = [15, 25]
    process_time_options = [[1, 5], [4, 20], [8, 40]]
    arrival_time_options = [[0, 0]]



    problems_dir = ".\GeneratedProblems_" + time.strftime("%Y%m%d%H%M")

    if not os.path.exists(problems_dir):
        os.mkdir(problems_dir)

    tests_per_combination = 10
    for j in jobs_options:
        for d in due_date_options:
            for m in machines_options:
                for p in process_time_options:
                    for a in arrival_time_options:
                        for t in range(0, tests_per_combination):
                            problem = generate_problem(m, j, d, p, a, [1, m])
                            save_problem_to_file(problem, os.path.join(
                                problems_dir, "m{0:02}j{1:02}d{2:02}p{3:02}_{4}.csv".format(m, j, d, p[1], t)))
                            # problem_f2 = multiply_time_units(problem, 2)
                            # save_problem_to_file(problem_f2, os.path.join(
                            #     problems_dir, "m{0:02}j{1:02}d{2:02}_{3}_f2.csv".format(m, j, d, t)))
                            # problem_f3 = multiply_time_units(problem, 3)
                            # save_problem_to_file(problem_f3, os.path.join(
                            #     problems_dir, "m{0:02}j{1:02}d{2:02}_{3}_f3.csv".format(m, j, d, t)))
                            # problem_f4 = multiply_time_units(problem, 4)
                            # save_problem_to_file(problem_f4, os.path.join(
                            #     problems_dir, "m{0:02}j{1:02}d{2:02}_{3}_f4.csv".format(m, j, d, t)))
                            # problem_f5 = multiply_time_units(problem, 5)
                            # save_problem_to_file(problem_f5, os.path.join(
                            #     problems_dir, "m{0:02}j{1:02}d{2:02}_{3}_f5.csv".format(m, j, d, t)))