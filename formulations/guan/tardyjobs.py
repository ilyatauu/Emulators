import time
from formulations import algorithms
from formulations import structures


def get_formulation(cplex_class, emulators_data):
    """ Get formulation for finding minimal number of tardy jobs problem
    :param cplex_class: class of type cplex.Cplex, to be populated by formulations
    :param emulators_data: emulators data problem
    :return: A formulation model object.
    """

    print "start preparation"
    formulation_model = structures.FormulationModel()
    start_preparation = time.time()

    jobs = [i.job_id for i in emulators_data.jobs_info]
    processtimes = [i.processtime for i in emulators_data.jobs_info]
    duedates = [i.duedate for i in emulators_data.jobs_info]
    sizes = [i.size for i in emulators_data.jobs_info]
    readytimes = [i.readytime for i in emulators_data.jobs_info]

    number_of_boards = emulators_data.boards_number

    if not hasattr(emulators_data, "maximum_t_value") or emulators_data.maximum_t_value is None:
        max_t = algorithms.get_edr_single_machine_max_time(emulators_data.jobs_info)
    else:
        max_t = emulators_data.maximum_t_value

    # defined constants
    penalty_weight = 1
    # tardiness_weight = EmulatorsCplexSolverRPFGuan.tardiness_weight

    cplex_solver = cplex_class

    # set the objective to minimize  or maximize
    cplex_solver.objective.set_sense(cplex_solver.objective.sense.minimize)

    # ############ Add variables  ##################################
    print "Adding variables .. "
    vars_map = dict()

    # uj variables, start processing time of job j
    variable_names = ['u{0}'.format(j) for j in jobs]
    cplex_solver.variables.add(
        obj=[0] * len(variable_names), types="C" * len(variable_names),
        lb=[0] * len(variable_names), names=variable_names)
    vars_map.update([('u{0}'.format(j), cplex_solver.variables.get_indices('u{0}'.format(j))) for j in jobs])

    # vj variables, start processing board of job j
    variable_names = ['v{0}'.format(j) for j in jobs]
    cplex_solver.variables.add(obj=[0] * len(variable_names), types="C" * len(variable_names),
                               lb=[0] * len(variable_names), names=variable_names)
    vars_map.update([('v{0}'.format(j), cplex_solver.variables.get_indices('v{0}'.format(j))) for j in jobs])

    # c_j variables, job completion time
    variable_names = ['c{0}'.format(j) for j in jobs]
    cplex_solver.variables.add(obj=[0] * len(variable_names), types="C" * len(variable_names), names=variable_names)
    vars_map.update([('c{0}'.format(j), cplex_solver.variables.get_indices('c{0}'.format(j))) for j in jobs])

    # precedence variables between job j and job i, on time basis
    variable_names = ['ll{0},{1}'.format(j, i) for j in jobs for i in jobs]
    cplex_solver.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
    vars_map.update(
        [('ll{0},{1}'.format(j, i),
          cplex_solver.variables.get_indices('ll{0},{1}'.format(j, i))) for j in jobs for i in jobs])

    # precedence variables between job j and job i, on boards basis
    variable_names = ['bb{0},{1}'.format(j, i) for j in jobs for i in jobs]
    cplex_solver.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
    vars_map.update(
        [('bb{0},{1}'.format(j, i),
          cplex_solver.variables.get_indices('bb{0},{1}'.format(j, i))) for j in jobs for i in jobs])

    # Uj variables
    variable_names = ['U{0}'.format(j) for j in jobs]
    cplex_solver.variables.add(obj=[penalty_weight] * len(variable_names), types="B" * len(variable_names),
                               names=variable_names)
    vars_map.update([('U{0}'.format(j), cplex_solver.variables.get_indices('U{0}'.format(j))) for j in jobs])

    # ############ Add Constraints  ##################################
    print "Adding constraints ... "

    # constraints for relative position

    for i in jobs:
        for j in jobs:
            if i == j:
                continue
            cplex_solver.linear_constraints.add(lin_expr=[
                [[vars_map['u' + repr(j)], vars_map['u' + repr(i)], vars_map['ll{0},{1}'.format(i, j)]],
                 [1, -1, -max_t]]], senses="G", rhs=[processtimes[i] - max_t])

            cplex_solver.linear_constraints.add(lin_expr=[
                [[vars_map['v' + repr(j)], vars_map['v' + repr(i)], vars_map['bb{0},{1}'.format(i, j)]],
                 [1, -1, -1 * number_of_boards]]], senses="G", rhs=[sizes[i] - number_of_boards])

            if i < j:
                continue
            cplex_solver.linear_constraints.add(
                lin_expr=[[[vars_map['ll{0},{1}'.format(i, j)], vars_map['ll{0},{1}'.format(j, i)],
                            vars_map['bb{0},{1}'.format(i, j)], vars_map['bb{0},{1}'.format(j, i)]], [1, 1, 1, 1]]],
                senses="G", rhs=[1])

            cplex_solver.linear_constraints.add(
                lin_expr=[[[vars_map['ll{0},{1}'.format(i, j)], vars_map['ll{0},{1}'.format(j, i)]], [1, 1]]],
                senses="L", rhs=[1])

            cplex_solver.linear_constraints.add(
                lin_expr=[[[vars_map['bb{0},{1}'.format(i, j)], vars_map['bb{0},{1}'.format(j, i)]], [1, 1]]],
                senses="L", rhs=[1])

    for j in jobs:
        cplex_solver.linear_constraints.add(
            lin_expr=[[[vars_map['u' + repr(j)], vars_map['c' + repr(j)]], [1, -1]]],
            senses="E", rhs=[-1 * processtimes[j]])
        cplex_solver.linear_constraints.add(
            lin_expr=[[[vars_map['u' + repr(j)]], [1]]], senses="G", rhs=[readytimes[j]])
        cplex_solver.linear_constraints.add(
            lin_expr=[[[vars_map['v' + repr(j)]], [1]]], senses="L",
            rhs=[number_of_boards - sizes[j]], names=['v' + repr(j)])

    # constraint of whether we need to have penalty for this job
    constraints = [[[vars_map['U' + repr(j)], vars_map['c' + repr(j)]], [max_t, -1]] for j in jobs]
    cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints),
                                        rhs=[-1 * duedates[j] for j in jobs], names=["Up" + repr(j) for j in jobs])

    # add penalty lower bound if exists
    if hasattr(emulators_data,"total_penalty_lower_bound") and emulators_data.total_penalty_lower_bound is not None:
        lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
        cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="G",
                                            rhs=[emulators_data.total_penalty_lower_bound])

    # add penalty upper bound if exists
    if hasattr(emulators_data, "total_penalty_upper_bound") and emulators_data.total_penalty_upper_bound is not None:
        lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
        cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="L",
                                            rhs=[emulators_data.total_penalty_upper_bound])

    end_preparation = time.time()
    print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

    formulation_model.vars_map = vars_map
    formulation_model.cplex_class = cplex_solver
    formulation_model.model_build_time = end_preparation - start_preparation

    return formulation_model


def add_decision_vars_constraints(formulation_model,  constraint_dict):
    cplex_class = formulation_model.cplex_class
    vars_map = formulation_model.vars_map
    for k in constraint_dict:
        # add time constraint
        if constraint_dict[k][0] == 1:
            cplex_class.linear_constraints.add(
                lin_expr=[[[vars_map['ll' + k]], [1]]],
                senses="E", rhs=[1])
        if constraint_dict[k][1] == 1:
            cplex_class.linear_constraints.add(
                lin_expr=[[[vars_map['bb' + k]], [1]]],
                senses="E", rhs=[1])

    return formulation_model
