from formulations import algorithms
from formulations import structures
import time

def get_formulation(cplex_class, emulators_data):
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
    vars_map = dict()
    # Xi,j,t variable
    variable_names = ['x{0},{1},{2}'.format(j, m, t)
                      for j in jobs for m in range(machines) for t in range(max_time)]
    variable_obj = [min(1, max((t + processtimes[j]) - duedates[j], 0)) for j in jobs for m in range(machines) for t
                    in range(max_time)]
    cplex_class.variables.add(obj=variable_obj, types="B" * len(variable_names), names=variable_names)
    vars_map.update(
        [('x{0},{1},{2}'.format(j, m, t), cplex_class.variables.get_indices('x{0},{1},{2}'.format(j, m, t))) for j
         in jobs for m in range(machines) for t in range(max_time)])

    # ############ Add Constraints  ##################################
    print "Adding constraints ... "

    # Every job must run once
    constraints = [[v, [1] * len(v)] for j in jobs for v in
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
                                               rhs=[1], names=["m:{0};t:{1}".format(m, t)])
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
                                           rhs=[machines - sizes[j]], names=["bstart(j:{0})".format(j)])
        # add readiness constraint
        cplex_class.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="G",
                                           rhs=[readytimes[j]], names=["readiness(j:{0})".format(j)])

        # reset lists
        sum_over_xjmt_ind = []
        sum_over_xjmt_val_m = []
        sum_over_xjmt_val_t = []

    end_preparation = time.time()
    print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

    formulation_model = structures.FormulationModel()

    formulation_model.vars_map = vars_map
    formulation_model.max_time = max_time
    formulation_model.cplex_class = cplex_class
    formulation_model.model_build_time = end_preparation - start_preparation

    return formulation_model
