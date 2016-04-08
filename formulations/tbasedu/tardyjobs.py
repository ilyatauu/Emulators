from formulations import algorithms
from formulations import structures
import time


def get_formulation(cplex_class, emulators_data, jobs_constraints=[]):
    """ solve_number_of_tardy_jobs functions """
    print "start preparation"

    start_preparation = time.time()
    jobs = [i.job_id for i in emulators_data.jobs_info]
    processtimes = [i.processtime for i in emulators_data.jobs_info]
    duedates = [i.duedate for i in emulators_data.jobs_info]
    sizes = [i.size for i in emulators_data.jobs_info]
    readytimes = [i.readytime for i in emulators_data.jobs_info]

    machines = emulators_data.boards_number

    if not hasattr(emulators_data, "maximum_t_value") or emulators_data.maximum_t_value is None:
        max_time = algorithms.get_edr_single_machine_max_time(emulators_data.jobs_info)
    else:
        max_time = emulators_data.maximum_t_value

    print "max_time:" + repr(max_time)

    # set the objective to minimize  or maximize
    cplex_class.objective.set_sense(cplex_class.objective.sense.minimize)

    # ############ Add variables  ##################################
    print "Adding variables .. "
    big_number = 1000000
    penalty_weight = 1
    vars_map = dict()
    max_duedate = max(duedates)
    max_time = max_duedate
    # Xi,j,t variable
    variable_names = ['x{0},{1},{2}'.format(j, m, t)
                      for j in jobs for m in range(machines) for t in range(max_time)]

    variable_obj = []
    cplex_class.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
    vars_map.update(
        [('x{0},{1},{2}'.format(j, m, t), cplex_class.variables.get_indices('x{0},{1},{2}'.format(j, m, t))) for j
         in jobs for m in range(machines) for t in range(max_time)])

    # Uj variables
    variable_names = ['U{0}'.format(j) for j in jobs]
    cplex_class.variables.add(obj=[1] * len(variable_names), types="B" * len(variable_names), names=variable_names)
    vars_map.update([('U{0}'.format(j), cplex_class.variables.get_indices('U{0}'.format(j))) for j in jobs])

    # ############ Add Constraints  ##################################
    print "Adding constraints ... "

    # Every job must run once,
    constraints = [[v + [vars_map['U{0}'.format(j)]], [1] * (len(v)+1)] for j in jobs for v in
                   [[vars_map['x{0},{1},{2}'.format(j, m, t)] for m in range(machines) for t in range(max_time)]]]

    cplex_class.linear_constraints.add(lin_expr=constraints, senses="E" * len(constraints), rhs=[1] * len(constraints))

    # On each board at each time t, only one job can run
    start_time = time.time()
    constraint_v = []
    for m in range(machines):
        for t in range(max_time):
            for jj in jobs:
                for mm in range(max(0, m - sizes[jj] + 1), m + 1):
                    for tt in range(max(0, t - processtimes[jj] + 1), t + 1):
                        constraint_v.append(vars_map['x{0},{1},{2}'.format(jj, mm, tt)])

            cplex_class.linear_constraints.add(lin_expr=[[constraint_v, [1] * len(constraint_v)]], senses="L",
                                               rhs=[1], names=["m{0};t{1}".format(m, t)])
            constraint_v = []
    end_time = time.time()
    print end_time - start_time

    # Prepare other constraints
    sum_over_xjmt_ind = []
    sum_over_xjmt_val_m = []
    sum_over_xjmt_val_t = []

    for j in jobs:
        for m in range(machines):
            for t in range(max_time):
                sum_over_xjmt_ind.append(vars_map['x{0},{1},{2}'.format(j, m, t)])
                sum_over_xjmt_val_m.append(m)
                sum_over_xjmt_val_t.append(t)

        # add board start constraint
        cplex_class.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_m]], senses="L",
                                           rhs=[machines - sizes[j]], names=["bstart(j{0})".format(j)])
        # add readiness constraint
        cplex_class.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="G",
                                           rhs=[readytimes[j]], names=["readiness(j{0})".format(j)])

        # reset lists
        sum_over_xjmt_ind = []
        sum_over_xjmt_val_m = []
        sum_over_xjmt_val_t = []

    # Nullify impossible xj,m,t
    constraints = [[[vars_map['x{0},{1},{2}'.format(j, m, t)]], [1]]
                   for j in jobs for m in range(machines)
                   for t in range(max_time)
                   if t > duedates[j] - processtimes[j] or t < readytimes[j]]

    cplex_class.linear_constraints.add(lin_expr=constraints, senses="E"*len(constraints), rhs=[0]*len(constraints))

    # Job specific constraints
    for c in jobs_constraints:
        if c.start_time is not None and c.first_board is not None:
            # Job must start on time c.start_time and board c.first_board
            x = vars_map['x{0},{1},{2}'.format(c.job_id, c.first_board, c.start_time)]
            cplex_class.linear_constraints.add(lin_expr=[[[x],[1]]], senses="E",
                                               rhs=[1], names=["scheduled(j{})".format(c.job_id)])
        elif c.start_time is not None:
            # Job must start on time c.start_time
            ez = [vars_map['x{0},{1},{2}'.format(c.job_id, m, c.start_time)] for m in range(machines)]
            cplex_class.linear_constraints.add(lin_expr=[[ez, [1]*len(ez)]], senses="E",
                                               rhs=[1], names=["scheduled(j{})".format(c.job_id)])
        elif c.first_board is not None:
            # Job must start on machine c.first_board
            ez = [vars_map['x{0},{1},{2}'.format(c.job_id, c.first_board, t)] for m in range(max_time)]
            cplex_class.linear_constraints.add(lin_expr=[[ez, [1]*len(ez)]], senses="E",
                                               rhs=[1], names=["scheduled(j{})".format(c.job_id)])
        elif c.duedate is not None:
            # Job must be finished before c.duedate, same as job must start before time x

            ez_vars = []
            ez_koff = []
            processtime = filter(lambda x: x.job_id == c.job_id, emulators_data.jobs_info)[0].processtime
            for m in range(machines):
                for t in range(max_time):
                    ez_vars.append(vars_map['x{0},{1},{2}'.format(c.job_id, m, t)])
                    ez_koff.append(t)
            cplex_class.linear_constraints.add(lin_expr=[[ez_vars, ez_koff]], senses="L",
                                               rhs=[c.duedate - processtime], names=["scheduled(j{})".format(c.job_id)])

    end_preparation = time.time()
    print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

    formulation_model = structures.FormulationModel()

    formulation_model.vars_map = vars_map
    formulation_model.max_time = max_time
    formulation_model.cplex_class = cplex_class
    formulation_model.model_build_time = end_preparation - start_preparation

    return formulation_model
