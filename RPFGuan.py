import cplex
import time
import common


class EmulatorsCplexSolverRPFGuan(object):
    """description of class"""

    jobs_data = [(0, 1, 7, 4, 0), (1, 2, 18, 8, 0), (2, 4, 24, 5, 0), (3, 6, 7, 5, 0), (4, 5, 15, 5, 0),
                 (5, 5, 16, 5, 0), (6, 3, 21, 9, 0), (7, 10, 13, 5, 0), (8, 7, 23, 6, 0), (9, 2, 3, 8, 0),
                 (10, 4, 4, 1, 0), (11, 2, 15, 7, 0), (12, 5, 7, 6, 0), (13, 5, 6, 9, 0), (14, 7, 11, 1, 0)]
    # jobs_data = [(0,10,13,7,0),(1,9,11,6,0),(2,8,12,7,0),(3,7,8,7,0),
    # (4,6,7,4,0),(5,6,8,7,0),(6,4,11,3,0),(7,8,8,5,0),(8,5,13,2,0),(9,4,14,6,0)]
    number_of_boards = 15
    current_best_objective = None
    current_best_penalty = None
    lazy_constraints = set()
    lazy_start_objective = None
    lazy_start_penlaty = None
    vars_map = dict()
    register_callbacks = False
    maximum_t_value = None
    time_divider = None
    penalty_weight = 1
    tardiness_weight = 1
    total_penalty_lower_bound = None
    total_penalty_upper_bound = None

    @staticmethod
    def clean():
        EmulatorsCplexSolverRPFGuan.jobs_data = []
        EmulatorsCplexSolverRPFGuan.number_of_boards = None
        EmulatorsCplexSolverRPFGuan.current_best_objective = None
        EmulatorsCplexSolverRPFGuan.current_best_penalty = None
        EmulatorsCplexSolverRPFGuan.lazy_constraints = set()
        EmulatorsCplexSolverRPFGuan.lazy_start_objective = None
        EmulatorsCplexSolverRPFGuan.lazy_start_penlaty = None
        EmulatorsCplexSolverRPFGuan.vars_map = dict()
        EmulatorsCplexSolverRPFGuan.register_callbacks = False
        EmulatorsCplexSolverRPFGuan.maximum_t_value = None
        EmulatorsCplexSolverRPFGuan.time_divider = None
        EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound = None
        EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound = None

    @property
    def solve(self):

        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        processtimes = [i[1] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        duedates = [i[2] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        sizes = [i[3] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        readytimes = [i[4] for i in EmulatorsCplexSolverRPFGuan.jobs_data]

        number_of_boards = EmulatorsCplexSolverRPFGuan.number_of_boards

        if EmulatorsCplexSolverRPFGuan.maximum_t_value is None:
            max_t = common.get_edr_single_machine_max_time(EmulatorsCplexSolverRPFGuan.jobs_data)
        else:
            max_t = EmulatorsCplexSolverRPFGuan.maximum_t_value

        # defined constants
        penalty_weight = EmulatorsCplexSolverRPFGuan.penalty_weight
        tardiness_weight = EmulatorsCplexSolverRPFGuan.tardiness_weight

        cplex_solver = cplex.Cplex()

        # set the objective to minimize  or maximize
        cplex_solver.objective.set_sense(cplex_solver.objective.sense.minimize)

        # set time limit to 2 hours
        cplex_solver.parameters.timelimit.set(600)

        cplex_solver.parameters.parallel.set(1)
        cplex_solver.parameters.threads.set(4)

        # set node log interval to 10
        cplex_solver.parameters.mip.interval.set(10)

        # ############ Add variables  ##################################
        print "Adding variables .. "
        vars_map = EmulatorsCplexSolverRPFGuan.vars_map

        # uj variables, start processing time of job j
        variable_names = ['u{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="C" * len(variable_names),
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
        vars_map.update([('ll{0},{1}'.format(j, i),
                          cplex_solver.variables.get_indices('ll{0},{1}'.format(j, i))) for j in jobs for i in jobs])

        # precedence variables between job j and job i, on boards basis
        variable_names = ['bb{0},{1}'.format(j, i) for j in jobs for i in jobs]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
        vars_map.update(
            [('bb{0},{1}'.format(j, i), cplex_solver.variables.get_indices('bb{0},{1}'.format(j, i))) for j in jobs for
             i in jobs])

        # Uj variables
        variable_names = ['U{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[penalty_weight] * len(variable_names), types="B" * len(variable_names),
                                   names=variable_names)
        vars_map.update([('U{0}'.format(j), cplex_solver.variables.get_indices('U{0}'.format(j))) for j in jobs])

        # Tj variables
        variable_names = ['T{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[tardiness_weight] * len(variable_names), types="C" * len(variable_names),
                                   names=variable_names, lb=[0] * len(variable_names))
        vars_map.update([('T{0}'.format(j), cplex_solver.variables.get_indices('T{0}'.format(j))) for j in jobs])

        # ############ Add Constraints  ##################################
        print "Adding constraints ... "

        # constraints for relative position

        for i in jobs:
            for j in jobs:
                if i == j:
                    continue
                cplex_solver.linear_constraints.add(
                    lin_expr=[
                        [[vars_map['u' + repr(j)],
                          vars_map['u' + repr(i)], vars_map['ll{0},{1}'.format(i, j)]], [1, -1, -max_t]]],
                    senses="G", rhs=[processtimes[i] - max_t])

                cplex_solver.linear_constraints.add(
                    lin_expr=[
                        [[vars_map['v' + repr(j)], vars_map['v' + repr(i)], vars_map['bb{0},{1}'.format(i, j)]],
                         [1, -1, -1 * number_of_boards]]],
                    senses="G", rhs=[sizes[i] - number_of_boards])

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
            cplex_solver.linear_constraints.add(lin_expr=[[[vars_map['u' + repr(j)]], [1]]], senses="G",
                                                rhs=[readytimes[j]])
            cplex_solver.linear_constraints.add(lin_expr=[[[vars_map['v' + repr(j)]], [1]]], senses="L",
                                                rhs=[number_of_boards - sizes[j]], names=['v' + repr(j)])

        # constraint of whether we need to have penalty for this job
        constraints = [[[vars_map['U' + repr(j)], vars_map['c' + repr(j)]], [max_t, -1]] for j in jobs]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints),
                                            rhs=[-1 * duedates[j] for j in jobs], names=["Up" + repr(j) for j in jobs])

        # Tardinesss of job j
        constraints = [[[vars_map['T' + repr(j)], vars_map['c' + repr(j)]], [1, -1]] for j in jobs]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints),
                                            rhs=[-1 * duedates[j] for j in jobs])

        # add penalty lower bound if exists
        if EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="G",
                                                rhs=[EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound])

        # add penalty upper bound if exists
        if EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="L",
                                                rhs=[EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound])

        end_preparation = time.time()
        print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

        cplex_solver.write("rpfguan.lp")
        start_solve = time.time()
        cplex_solver.solve()
        end_solve = time.time()

        print "Solved in " + repr(end_solve - start_solve)

        print cplex_solver.solution.get_status()

        result = common.CplexResult()
        # if infeasible
        if cplex_solver.solution.get_status() == 103:
            result.feasible = False
            result.optimal = True
            return result
        if cplex_solver.solution.get_status() == 108:
            result.feasible = False
            result.optimal = False
            return result

        if cplex_solver.solution.get_status() == 107:
            result.feasible = True
            result.optimal = False
        elif cplex_solver.solution.get_status() == 101 or cplex_solver.solution.get_status() == 102:
            result.feasible = True
            result.optimal = True

        jon_info_list = []

        for j in jobs:
            info = common.JobInfo()
            info.job_id = j
            info.start_time = cplex_solver.solution.get_values(vars_map['u' + repr(j)])
            info.first_board = cplex_solver.solution.get_values(vars_map['v' + repr(j)])
            info.finish_time = info.start_time + processtimes[j]
            info.tardiness = cplex_solver.solution.get_values(vars_map['T' + repr(j)])
            jon_info_list.append(info)

        result.total_penalty = int(round(sum([cplex_solver.solution.get_values('U' + repr(j)) for j in jobs])))
        result.total_tardiness = int(round(sum([cplex_solver.solution.get_values('T' + repr(j)) for j in jobs])))
        result.objective_value = int(round(cplex_solver.solution.get_objective_value()))
        result.relative_gap = cplex_solver.solution.MIP.get_mip_relative_gap()
        result.job_info = jon_info_list

        return result

    def solve_number_of_tardy_jobs(self):
        """ solve_number_of_tardy_jobs functions """
        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        processtimes = [i[1] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        duedates = [i[2] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        sizes = [i[3] for i in EmulatorsCplexSolverRPFGuan.jobs_data]
        readytimes = [i[4] for i in EmulatorsCplexSolverRPFGuan.jobs_data]

        number_of_boards = EmulatorsCplexSolverRPFGuan.number_of_boards

        if EmulatorsCplexSolverRPFGuan.maximum_t_value is None:
            max_t = common.get_edr_single_machine_max_time(EmulatorsCplexSolverRPFGuan.jobs_data)
        else:
            max_t = EmulatorsCplexSolverRPFGuan.maximum_t_value

        # defined constants
        penalty_weight = EmulatorsCplexSolverRPFGuan.penalty_weight
        # tardiness_weight = EmulatorsCplexSolverRPFGuan.tardiness_weight

        cplex_solver = cplex.Cplex()

        # set the objective to minimize  or maximize
        cplex_solver.objective.set_sense(cplex_solver.objective.sense.minimize)

        # set time limit to 2 hours
        cplex_solver.parameters.timelimit.set(600)

        cplex_solver.parameters.parallel.set(1)
        cplex_solver.parameters.threads.set(4)

        # set node log interval to 10
        cplex_solver.parameters.mip.interval.set(10)

        # ############ Add variables  ##################################
        print "Adding variables .. "
        vars_map = EmulatorsCplexSolverRPFGuan.vars_map

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
        if EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="G",
                                                rhs=[EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound])

        # add penalty upper bound if exists
        if EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="L",
                                                rhs=[EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound])

        end_preparation = time.time()
        print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

        cplex_solver.write("rpfguan.lp")
        start_solve = time.time()
        cplex_solver.solve()
        end_solve = time.time()

        print "Solved in " + repr(end_solve - start_solve)

        print cplex_solver.solution.get_status()

        result = common.CplexResult()
        # if infeasible
        if cplex_solver.solution.get_status() == 103:
            result.feasible = False
            result.optimal = True
            return result
        if cplex_solver.solution.get_status() == 108:
            result.feasible = False
            result.optimal = False
            return result

        if cplex_solver.solution.get_status() == 107:
            result.feasible = True
            result.optimal = False
        elif cplex_solver.solution.get_status() == 101 or cplex_solver.solution.get_status() == 102:
            result.feasible = True
            result.optimal = True

        job_info_list = []

        for j in jobs:
            info = common.JobInfo()
            info.job_id = j
            info.start_time = int(round(cplex_solver.solution.get_values(vars_map['u' + repr(j)])))
            info.first_board = int(round(cplex_solver.solution.get_values(vars_map['v' + repr(j)])))
            info.finish_time = info.start_time + processtimes[j]
            job_info_list.append(info)

        result.total_penalty = int(round(sum([cplex_solver.solution.get_values('U' + repr(j)) for j in jobs])))
        result.objective_value = int(round(cplex_solver.solution.get_objective_value()))
        result.job_info = job_info_list
        result.relative_gap = cplex_solver.solution.MIP.get_mip_relative_gap()
        result.model_build_time = end_preparation - start_preparation

        return result


def solve_cplex_only(jobs_data, number_of_boards, props):
    start_time = time.time()
    EmulatorsCplexSolverRPFGuan.clean()
    cplex_sover = EmulatorsCplexSolverRPFGuan()
    EmulatorsCplexSolverRPFGuan.jobs_data = jobs_data
    EmulatorsCplexSolverRPFGuan.number_of_boards = number_of_boards
    EmulatorsCplexSolverRPFGuan.total_penalty_lower_bound = props.total_penalty_lower_bound
    EmulatorsCplexSolverRPFGuan.total_penalty_upper_bound = props.total_penalty_upper_bound

    cplex_result = cplex_sover.solve_number_of_tardy_jobs()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result

# ************* Main Program ************************
if __name__ == "__main__":
    f = "C:\\Users\\izaides\\Documents\\Visual Studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201410181246\\RecheckFolder\\m15j10d15_2.csv"
    common.solve_and_save(f, "RPFGuan", solve_cplex_only)