import time
import cplex
from cplex.callbacks import LazyConstraintCallback
import threading
import common
import cpbased
import math


class EmulatorsLazyCallback(LazyConstraintCallback):
    def __call__(self):

        # We will use this to make the callback threadsafe
        lock = threading.Lock()
        jobs = [i[0] for i in TBasedCplexSolver.jobs_data]
        total_penalty = round(sum([self.get_values('U' + repr(j)) for j in jobs]))
        objective_value = self.get_objective_value()

        print "MIP Solution, objective: {0}; total_penalty: {1}".format(objective_value, total_penalty)

        # start thread safe block (inside try .. finally)
        try:
            lock.acquire()
            print "TBasedCplexSolver.lazy_start_objective = " + repr(TBasedCplexSolver.lazy_start_objective)
            print "objective_value = " + repr(objective_value)
            if TBasedCplexSolver.lazy_start_objective is not None \
                    and TBasedCplexSolver.lazy_start_objective <= round(objective_value):
                print "Lazy call back, have nothing to do"
                return
        finally:
            # end of thread safe block
            lock.release()

        solver = cpbased.EmulatorsCpSolver()
        solver.total_penalty = total_penalty
        solver.objective_value = objective_value
        solver.time_limit = 3
        cp_result = solver.solve(TBasedCplexSolver.jobs_data, TBasedCplexSolver.number_of_boards)

        if cp_result.feasible is False:
            "CP Did not find any feasible solution"
            return

        print "CpSolution: penalty:" + repr(cp_result.total_penalty) + "; objective: " + repr(cp_result.objective_value)

        penalty_id = "p" + repr(cp_result.total_penalty)
        objective_id = "o" + repr(cp_result.objective_value)

        # start thread safe block
        # start thread safe block (inside try .. finally)
        try:
            lock.acquire()

            # objecttive_exists = objective_id in TBasedCplexSolver.lazy_constraints
            penalty_exsits = penalty_id in TBasedCplexSolver.lazy_constraints

            if TBasedCplexSolver.lazy_start_objective is None \
                    or TBasedCplexSolver.lazy_start_objective >= cp_result.objective_value:
                TBasedCplexSolver.lazy_start_objective = int(round(cp_result.objective_value))
                TBasedCplexSolver.lazy_start_penlaty = int(round(cp_result.total_penalty))
                TBasedCplexSolver.current_best_objective = TBasedCplexSolver.lazy_start_objective
                TBasedCplexSolver.current_best_penalty = TBasedCplexSolver.lazy_start_penlaty

            if penalty_exsits is False:
                print "adding constraint " + penalty_id
                TBasedCplexSolver.lazy_constraints.add(penalty_id)
                # add late jobs constraints
                self.add(constraint=[['U' + repr(j) for j in jobs], [1] * len(jobs)], sense="L",
                         rhs=int(cp_result.total_penalty))

            if objective_id not in TBasedCplexSolver.lazy_constraints:
                TBasedCplexSolver.lazy_constraints.add(objective_id)
                print "adding constraint " + objective_id
                # add objective value constraint
                self.add(constraint=[['U' + repr(j) for j in jobs] + ['T' + repr(j) for j in jobs],
                                     [1000] * len(jobs) + [1] * len(jobs)], sense="L",
                         rhs=int(cp_result.objective_value))
        finally:
            # end of thread safe block
            lock.release()


class TBasedCplexSolver(object):
    """description of class"""

    jobs_data = []
    number_of_boards = None
    current_best_objective = None
    current_best_penalty = None
    lazy_constraints = set()
    lazy_start_objective = None
    lazy_start_penlaty = None
    vars_map = dict()
    register_callbacks = False
    maximum_t_value = None
    time_divider = None
    total_penalty_lower_bound = None
    total_penalty_upper_bound = None

    @staticmethod
    def clean():
        TBasedCplexSolver.jobs_data = []
        TBasedCplexSolver.number_of_boards = None
        TBasedCplexSolver.current_best_objective = None
        TBasedCplexSolver.current_best_penalty = None
        TBasedCplexSolver.lazy_constraints = set()
        TBasedCplexSolver.lazy_start_objective = None
        TBasedCplexSolver.lazy_start_penlaty = None
        vars_map = dict()
        TBasedCplexSolver.register_callbacks = False
        TBasedCplexSolver.maximum_t_value = None
        TBasedCplexSolver.time_divider = None
        TBasedCplexSolver.total_penalty_lower_bound = None
        TBasedCplexSolver.total_penalty_upper_bound = None

    def solve(self):

        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in TBasedCplexSolver.jobs_data]
        processtimes = [i[1] for i in TBasedCplexSolver.jobs_data]
        duedates = [i[2] for i in TBasedCplexSolver.jobs_data]
        sizes = [i[3] for i in TBasedCplexSolver.jobs_data]
        readytimes = [i[4] for i in TBasedCplexSolver.jobs_data]

        machines = TBasedCplexSolver.number_of_boards
        if TBasedCplexSolver.maximum_t_value is None:
            max_time = common.get_edr_single_machine_max_time(TBasedCplexSolver.jobs_data)
        else:
            max_time = TBasedCplexSolver.maximum_t_value

        print "max_time:" + repr(max_time)

        # defined constants
        penalty_weight = 1000
        tardiness_weight = 1

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
        vars_map = TBasedCplexSolver.vars_map
        # Xi,j,t variable
        variable_names = ['x{0},{1},{2}'.format(j, m, t)
                          for j in jobs for m in range(machines) for t in range(max_time)]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
        vars_map.update(
            [('x{0},{1},{2}'.format(j, m, t), cplex_solver.variables.get_indices('x{0},{1},{2}'.format(j, m, t))) for j
             in jobs for m in range(machines) for t in range(max_time)])

        # Uj variables
        variable_names = ['U{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[penalty_weight] * len(variable_names), types="B" * len(variable_names),
                                   names=variable_names)
        vars_map.update([('U{0}'.format(j), cplex_solver.variables.get_indices('U{0}'.format(j))) for j in jobs])

        # c_j variables
        variable_names = ['c{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="C" * len(variable_names), names=variable_names)
        vars_map.update([('c{0}'.format(j), cplex_solver.variables.get_indices('c{0}'.format(j))) for j in jobs])

        # Tj variables
        variable_names = ['T{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[tardiness_weight] * len(variable_names), types="C" * len(variable_names),
                                   names=variable_names, lb=[0] * len(variable_names))
        vars_map.update([('T{0}'.format(j), cplex_solver.variables.get_indices('T{0}'.format(j))) for j in jobs])

        # ############ Add Constraints  ##################################
        print "Adding constraints ... "

        # Add upper bound constraints
        if TBasedCplexSolver.current_best_objective is not None:
            TBasedCplexSolver.lazy_constraints.add("o" + repr(TBasedCplexSolver.current_best_objective))
            cplex_solver.linear_constraints.add(
                lin_expr=[[['U' + repr(j) for j in jobs] + ['T' + repr(j) for j in jobs],
                           [1000] * len(jobs) + [1] * len(jobs)]],
                senses=["L"], rhs=[int(TBasedCplexSolver.current_best_objective)])

        if TBasedCplexSolver.current_best_penalty is not None:
            TBasedCplexSolver.lazy_constraints.add("o" + repr(TBasedCplexSolver.current_best_penalty))
            cplex_solver.linear_constraints.add(lin_expr=[[['U' + repr(j) for j in jobs], [1] * len(jobs)]],
                                                senses=["L"], rhs=[int(TBasedCplexSolver.current_best_penalty)])

        # Every job must run once
        constraints = [[v, [1] * len(v)] for j in jobs for v in
                       [[vars_map['x{0},{1},{2}'.format(j, m, t)] for m in range(machines) for t in range(max_time)]]]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="E" * len(constraints),
                                            rhs=[1] * len(constraints))

        # On each board at each time t, only one job can run
        start_time = time.time()
        constraint_v = []
        for m in range(machines):
            for t in range(max_time):
                for jj in jobs:
                    for mm in range(max(0, m - sizes[jj] + 1), m + 1):
                        for tt in range(max(0, t - processtimes[jj] + 1), t + 1):
                            constraint_v.append(vars_map['x{0},{1},{2}'.format(jj, mm, tt)])

                cplex_solver.linear_constraints.add(lin_expr=[[constraint_v, [1] * len(constraint_v)]], senses="L",
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
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_m]], senses="L",
                                                rhs=[machines - sizes[j]], names=["bstart(j:{0})".format(j)])
            # add readiness constraint
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="G",
                                                rhs=[readytimes[j]], names=["readiness(j:{0})".format(j)])
            # add completion time constraint
            sum_over_xjmt_ind.append(cplex_solver.variables.get_indices('c' + repr(j)))
            sum_over_xjmt_val_t.append(-1)
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="E",
                                                rhs=[-1 * processtimes[j]], names=["completion(j:{0})".format(j)])
            # reset lists
            sum_over_xjmt_ind = []
            sum_over_xjmt_val_m = []
            sum_over_xjmt_val_t = []

        # constraint of whether we need to have penalty for this job
        constraints = [[[vars_map['U' + repr(j)], vars_map['T' + repr(j)]], [max_time, -1]] for j in jobs]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints), rhs=[0] * len(jobs),
                                            names=["Up" + repr(j) for j in jobs])

        # Tardinesss of job j
        constraints = [[[vars_map['T' + repr(j)], vars_map['c' + repr(j)]], [1, -1]] for j in jobs]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints),
                                            rhs=[-1 * duedates[j] for j in jobs])

        # add penalty lower bound if exists
        if TBasedCplexSolver.total_penalty_lower_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="G",
                                                rhs=[TBasedCplexSolver.total_penalty_lower_bound])

        # add penalty upper bound if exists
        if TBasedCplexSolver.total_penalty_upper_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses="L",
                                                rhs=[TBasedCplexSolver.total_penalty_upper_bound])

        if TBasedCplexSolver.register_callbacks is True:
            cplex_solver.register_callback(EmulatorsLazyCallback)
            pass

        end_preparation = time.time()
        print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

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
        # update divider if there was any
        if TBasedCplexSolver.time_divider is not None:
            div = TBasedCplexSolver.time_divider
        else:
            div = 1

        for j in jobs:
            for m in range(machines):
                for t in range(max_time):
                    if cplex_solver.solution.get_values(vars_map['x{0},{1},{2}'.format(j, m, t)]) >= 1 - 1e-06:
                        info = common.JobInfo()
                        info.job_id = j
                        info.start_time = int(math.floor(t * div))
                        info.finish_time = info.start_time + int(math.floor(processtimes[j] * div))
                        info.tardiness = int(math.floor(cplex_solver.solution.get_values('T' + repr(j)) * div))
                        info.first_board = m
                        info.finish_board = m + sizes[j]
                        job_info_list.append(info)

        result.total_penalty = int(round(sum([cplex_solver.solution.get_values('U' + repr(j)) for j in jobs])))
        result.total_tardiness = int(round(sum([cplex_solver.solution.get_values('T' + repr(j)) for j in jobs])))
        result.objective_value = int(round(cplex_solver.solution.get_objective_value()))
        result.relative_gap = cplex_solver.solution.MIP.get_mip_relative_gap()

        result.job_info = job_info_list

        return result

    def solve_number_of_tardy_jobs(self):
        """ solve_number_of_tardy_jobs functions """
        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in TBasedCplexSolver.jobs_data]
        processtimes = [i[1] for i in TBasedCplexSolver.jobs_data]
        duedates = [i[2] for i in TBasedCplexSolver.jobs_data]
        sizes = [i[3] for i in TBasedCplexSolver.jobs_data]
        readytimes = [i[4] for i in TBasedCplexSolver.jobs_data]

        machines = TBasedCplexSolver.number_of_boards
        if TBasedCplexSolver.maximum_t_value is None:
            max_time = common.get_edr_single_machine_max_time(TBasedCplexSolver.jobs_data)
        else:
            max_time = TBasedCplexSolver.maximum_t_value

        print "max_time:" + repr(max_time)

        # defined constants
        penalty_weight = 1
        # tardiness_weight = 1

        cplex_solver = cplex.Cplex()

        # set the objective to minimize  or maximize
        cplex_solver.objective.set_sense(cplex_solver.objective.sense.minimize)

        # set time limit to 10 minutes
        cplex_solver.parameters.timelimit.set(600)

        cplex_solver.parameters.parallel.set(1)
        cplex_solver.parameters.threads.set(4)

        # set node log interval to 10
        cplex_solver.parameters.mip.interval.set(10)

        # ############ Add variables  ##################################
        print "Adding variables .. "
        vars_map = TBasedCplexSolver.vars_map
        # Xi,j,t variable
        variable_names = ['x{0},{1},{2}'.format(j, m, t)
                          for j in jobs for m in range(machines) for t in range(max_time)]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="B" * len(variable_names), names=variable_names)
        vars_map.update(
            [('x{0},{1},{2}'.format(j, m, t), cplex_solver.variables.get_indices('x{0},{1},{2}'.format(j, m, t))) for j
             in jobs for m in range(machines) for t in range(max_time)])

        # Uj variables
        variable_names = ['U{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[penalty_weight] * len(variable_names), types="B" * len(variable_names),
                                   names=variable_names)
        vars_map.update([('U{0}'.format(j), cplex_solver.variables.get_indices('U{0}'.format(j))) for j in jobs])

        # c_j variables
        variable_names = ['c{0}'.format(j) for j in jobs]
        cplex_solver.variables.add(obj=[0] * len(variable_names), types="C" * len(variable_names), names=variable_names)
        vars_map.update([('c{0}'.format(j), cplex_solver.variables.get_indices('c{0}'.format(j))) for j in jobs])

        # ############ Add Constraints  ##################################
        print "Adding constraints ... "

        # Every job must run once
        constraints = [[v, [1] * len(v)] for j in jobs for v in
                       [[vars_map['x{0},{1},{2}'.format(j, m, t)] for m in range(machines) for t in range(max_time)]]]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="E" * len(constraints),
                                            rhs=[1] * len(constraints))

        # On each board at each time t, only one job can run
        start_time = time.time()
        constraint_v = []
        for m in range(machines):
            for t in range(max_time):
                for jj in jobs:
                    for mm in range(max(0, m - sizes[jj] + 1), m + 1):
                        for tt in range(max(0, t - processtimes[jj] + 1), t + 1):
                            constraint_v.append(vars_map['x{0},{1},{2}'.format(jj, mm, tt)])

                cplex_solver.linear_constraints.add(lin_expr=[[constraint_v, [1] * len(constraint_v)]], senses="L",
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
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_m]], senses="L",
                                                rhs=[machines - sizes[j]], names=["bstart(j:{0})".format(j)])
            # add readiness constraint
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="G",
                                                rhs=[readytimes[j]], names=["readiness(j:{0})".format(j)])
            # add completion time constraint
            sum_over_xjmt_ind.append(cplex_solver.variables.get_indices('c' + repr(j)))
            sum_over_xjmt_val_t.append(-1)
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="E",
                                                rhs=[-1 * processtimes[j]], names=["completion(j:{0})".format(j)])
            # reset lists
            sum_over_xjmt_ind = []
            sum_over_xjmt_val_m = []
            sum_over_xjmt_val_t = []

        # constraint of whether we need to have penalty for this job
        constraints = [[[vars_map['U' + repr(j)], vars_map['c' + repr(j)]], [max_time, -1]] for j in jobs]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="G" * len(constraints),
                                            rhs=[-1 * duedates[j] for j in jobs], names=["Up" + repr(j) for j in jobs])

        # add penalty lower bound if exists
        if TBasedCplexSolver.total_penalty_lower_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses=["G"],
                                                rhs=[TBasedCplexSolver.total_penalty_lower_bound])

        # add penalty upper bound if exists
        if TBasedCplexSolver.total_penalty_upper_bound is not None:
            lbconstraint = [[[vars_map['U' + repr(j)] for j in jobs], [1] * len(jobs)]]
            cplex_solver.linear_constraints.add(lin_expr=lbconstraint, senses=["L"],
                                                rhs=[TBasedCplexSolver.total_penalty_upper_bound])

        if TBasedCplexSolver.register_callbacks is True:
            cplex_solver.register_callback(EmulatorsLazyCallback)
            pass

        end_preparation = time.time()
        print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

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
        # update divider if there was any
        if TBasedCplexSolver.time_divider is not None:
            div = TBasedCplexSolver.time_divider
        else:
            div = 1

        for j in jobs:
            for m in range(machines):
                for t in range(max_time):
                    if cplex_solver.solution.get_values(vars_map['x{0},{1},{2}'.format(j, m, t)]) >= 1 - 1e-06:
                        info = common.JobInfo()
                        info.job_id = j
                        info.start_time = int(math.ceil(t * div))
                        info.finish_time = info.start_time + int(math.ceil(processtimes[j] * div))
                        info.first_board = m
                        info.finish_board = m + sizes[j]
                        job_info_list.append(info)

        result.total_penalty = int(round(sum([cplex_solver.solution.get_values('U' + repr(j)) for j in jobs])))
        result.objective_value = int(round(cplex_solver.solution.get_objective_value()))
        result.relative_gap = cplex_solver.solution.MIP.get_mip_relative_gap()

        result.job_info = job_info_list

        return result

    def solve_number_of_tardy_jobs_w(self):
        """ solve_number_of_tardy_jobs functions """
        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in TBasedCplexSolver.jobs_data]
        processtimes = [i[1] for i in TBasedCplexSolver.jobs_data]
        duedates = [i[2] for i in TBasedCplexSolver.jobs_data]
        sizes = [i[3] for i in TBasedCplexSolver.jobs_data]
        readytimes = [i[4] for i in TBasedCplexSolver.jobs_data]

        machines = TBasedCplexSolver.number_of_boards
        if TBasedCplexSolver.maximum_t_value is None:
            max_time = common.get_edr_single_machine_max_time(TBasedCplexSolver.jobs_data)
        else:
            max_time = TBasedCplexSolver.maximum_t_value

        print "max_time:" + repr(max_time)

        # defined constants
        # penalty_weight = 1
        # tardiness_weight = 1

        cplex_solver = cplex.Cplex()

        # set the objective to minimize  or maximize
        cplex_solver.objective.set_sense(cplex_solver.objective.sense.minimize)

        # set time limit to 10 minutes
        cplex_solver.parameters.timelimit.set(1800)

        cplex_solver.parameters.parallel.set(1)
        cplex_solver.parameters.threads.set(4)

        # set node log interval to 10
        cplex_solver.parameters.mip.interval.set(10)

        # ############ Add variables  ##################################
        print "Adding variables .. "
        vars_map = TBasedCplexSolver.vars_map
        # Xi,j,t variable
        variable_names = ['x{0},{1},{2}'.format(j, m, t)
                          for j in jobs for m in range(machines) for t in range(max_time)]
        variable_obj = [min(1, max((t + processtimes[j]) - duedates[j], 0)) for j in jobs for m in range(machines) for t
                        in range(max_time)]
        cplex_solver.variables.add(obj=variable_obj, types="B" * len(variable_names), names=variable_names)
        vars_map.update(
            [('x{0},{1},{2}'.format(j, m, t), cplex_solver.variables.get_indices('x{0},{1},{2}'.format(j, m, t))) for j
             in jobs for m in range(machines) for t in range(max_time)])

        # ############ Add Constraints  ##################################
        print "Adding constraints ... "

        # Every job must run once
        constraints = [[v, [1] * len(v)] for j in jobs for v in
                       [[vars_map['x{0},{1},{2}'.format(j, m, t)] for m in range(machines) for t in range(max_time)]]]
        cplex_solver.linear_constraints.add(lin_expr=constraints, senses="E" * len(constraints),
                                            rhs=[1] * len(constraints))

        # On each board at each time t, only one job can run
        start_time = time.time()
        constraint_v = []
        for m in range(machines):
            for t in range(max_time):
                for jj in jobs:
                    for mm in range(max(0, m - sizes[jj] + 1), m + 1):
                        for tt in range(max(0, t - processtimes[jj] + 1), t + 1):
                            constraint_v.append(vars_map['x{0},{1},{2}'.format(jj, mm, tt)])

                cplex_solver.linear_constraints.add(lin_expr=[[constraint_v, [1] * len(constraint_v)]], senses="L",
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
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_m]], senses="L",
                                                rhs=[machines - sizes[j]], names=["bstart(j:{0})".format(j)])
            # add readiness constraint
            cplex_solver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind, sum_over_xjmt_val_t]], senses="G",
                                                rhs=[readytimes[j]], names=["readiness(j:{0})".format(j)])

            # reset lists
            sum_over_xjmt_ind = []
            sum_over_xjmt_val_m = []
            sum_over_xjmt_val_t = []

        if TBasedCplexSolver.register_callbacks is True:
            cplex_solver.register_callback(EmulatorsLazyCallback)
            pass

        end_preparation = time.time()
        print "Preparation ended, took" + repr(end_preparation - start_preparation) + " seconds"

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
        # update divider if there was any
        if TBasedCplexSolver.time_divider is not None:
            div = TBasedCplexSolver.time_divider
        else:
            div = 1

        for j in jobs:
            for m in range(machines):
                for t in range(max_time):
                    if cplex_solver.solution.get_values(vars_map['x{0},{1},{2}'.format(j, m, t)]) >= 1 - 1e-06:
                        info = common.JobInfo()
                        info.job_id = j
                        info.start_time = int(math.ceil(t * div))
                        info.finish_time = info.start_time + int(math.ceil(processtimes[j] * div))
                        info.first_board = m
                        info.finish_board = m + sizes[j]
                        job_info_list.append(info)

        result.total_penalty = int(round(cplex_solver.solution.get_objective_value()))
        result.objective_value = int(round(cplex_solver.solution.get_objective_value()))
        result.relative_gap = cplex_solver.solution.MIP.get_mip_relative_gap()
        result.model_build_time = end_preparation - start_preparation
        result.model_solution_time = end_solve - start_solve

        result.job_info = job_info_list

        return result


def solve_cplex_only(jobs_data, number_of_boards, props):
    start_time = time.time()
    TBasedCplexSolver.clean()
    cplex_sover = TBasedCplexSolver()
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    TBasedCplexSolver.total_penalty_lower_bound = props.total_penalty_lower_bound
    TBasedCplexSolver.total_penalty_upper_bound = props.total_penalty_upper_bound

    cplex_result = cplex_sover.solve_number_of_tardy_jobs()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result


def solve_cplex_combined(jobs_data, number_of_boards):
    start_time = time.time()
    TBasedCplexSolver.clean()
    cplex_sover = TBasedCplexSolver()
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    # Use CP for upper bounds calculation
    cp_solver = cpbased.EmulatorsCpSolver()
    cp_result = cp_solver.solve(TBasedCplexSolver.jobs_data, TBasedCplexSolver.number_of_boards)
    TBasedCplexSolver.register_callbacks = True

    if cp_result.feasible:
        TBasedCplexSolver.current_best_penalty = cp_result.total_penalty
        TBasedCplexSolver.current_best_objective = cp_result.objective_value
        if cp_result.total_penalty > 0:
            edr_ordered = sorted(jobs_data, key=lambda y: y[1] + y[4], reverse=True)[0:cp_result.total_penalty]
            tardy_jobs = filter(lambda z: (z[1] + jobs_data[z[0]][1]) > jobs_data[z[0]][2], cp_result.jobs_results)
            TBasedCplexSolver.maximum_t_value = cp_result.schedule_completion_time - sum(
                [jobs_data[x[0]][1] for x in tardy_jobs]) + sum([x[1] for x in edr_ordered]) + max(
                [x[4] for x in edr_ordered])

        print "CP MaxT: " + repr(TBasedCplexSolver.maximum_t_value)
        print "CP Upper bound total_penalty: " + repr(cp_result.total_penalty)
        print "CP Upper bound objective value: " + repr(cp_result.objective_value)
    else:
        TBasedCplexSolver.maximum_t_value = common.get_edr_single_machine_max_time(TBasedCplexSolver.jobs_data)

    if TBasedCplexSolver.maximum_t_value > 50:
        div = TBasedCplexSolver.maximum_t_value / 50.0
        new_jobs_data = [
            [x[0], int(math.ceil(x[1] / div)), int(math.ceil(x[2] / div)), x[3], int(math.ceil(x[4] / div))] for x in
            TBasedCplexSolver.jobs_data]
        TBasedCplexSolver.jobs_data = new_jobs_data
        TBasedCplexSolver.time_divider = div
        print "Time discretization was made with divider of: " + repr(div)

    cplex_result = cplex_sover.solve()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result


def solve_cplex_timediscrete_combined(jobs_data, number_of_boards):
    start_time = time.time()
    TBasedCplexSolver.clean()
    cplex_sover = TBasedCplexSolver()
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    # Use time disretization in as first step
    if TBasedCplexSolver.maximum_t_value > 20:
        div = TBasedCplexSolver.maximum_t_value / 20.0
        new_jobs_data = [
            [x[0], int(math.ceil(x[1] / div)), int(math.ceil(x[2] / div)), x[3], int(math.ceil(x[4] / div))] for x in
            TBasedCplexSolver.jobs_data]
        TBasedCplexSolver.jobs_data = new_jobs_data
        TBasedCplexSolver.time_divider = div
    cplex_result = cplex_sover.solve()
    TBasedCplexSolver.clean()
    TBasedCplexSolver.maximum_t_value = max([x.finish_time for x in cplex_result.job_info])
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    cplex_result = cplex_sover.solve()

    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result


def solve_cplex__number_of_tardy_jobs_timedivider(jobs_data, number_of_boards, time_divider):
    start_time = time.time()
    TBasedCplexSolver.clean()
    cplex_sover = TBasedCplexSolver()
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    # Use time disretization in as first step
    new_jobs_data = [[x[0], int(math.ceil(x[1] / time_divider)), int(math.floor(x[2] / time_divider)), x[3],
                      int(math.ceil(x[4] / time_divider))] for x in TBasedCplexSolver.jobs_data]
    TBasedCplexSolver.jobs_data = new_jobs_data
    TBasedCplexSolver.time_divider = time_divider
    cplex_result = cplex_sover.solve_number_of_tardy_jobs()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result


def solve_cplex__number_of_tardy_jobs_w(jobs_data, number_of_boards, time_divider=None):
    if time_divider is None:
        time_divider = 1.0
    start_time = time.time()
    TBasedCplexSolver.clean()
    cplex_sover = TBasedCplexSolver()
    TBasedCplexSolver.jobs_data = jobs_data
    TBasedCplexSolver.number_of_boards = number_of_boards
    TBasedCplexSolver.time_divider = time_divider
    cplex_result = cplex_sover.solve_number_of_tardy_jobs_w()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result


def get_time_divided_jobs_data(jobs_data, time_divider):
    new_jobs_data = [[x[0], int(math.ceil(x[1] / time_divider)), int(math.floor(x[2] / time_divider)), x[3],
                      int(math.ceil(x[4] / time_divider))] for x in jobs_data]
    return new_jobs_data

# ************* Main Program ************************
if __name__ == "__main__":
    f = "C:\\Users\\izaides\\Documents\\Visual Studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201411192342\\m20j20d15_5.csv"
    # common.solve_and_save(f,"TBased",solve_cplex_only)
    data = common.load_data2(f)
    solve_cplex__number_of_tardy_jobs_timedivider(data[0], data[1], 10.0)
