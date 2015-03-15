import cplex
import time
import common
from cplex.callbacks import LazyConstraintCallback, UserCutCallback


class EmulatorsLazyCallback(LazyConstraintCallback):

    def __call__(self):
        vars_map = EmulatorsCplexSolverLayout.vars_map
        jobs_data = EmulatorsCplexSolverLayout.jobs_data
        number_of_boards = EmulatorsCplexSolverLayout.number_of_boards
        max_t = EmulatorsCplexSolverLayout.maximum_t_value

        len_jobs = len(jobs_data)
        xarr = [self.get_values(vars_map['x'+`j`]) for j in range(len_jobs)]
        yarr = [self.get_values(vars_map['y'+`j`]) for j in range(len_jobs)]

        for j in range(len_jobs):
            for i in range(len_jobs):
                if j<=i: continue

                if ((abs(xarr[j] - xarr[i]) < 0.5 * (jobs_data[j][1] + jobs_data[i][1])) 
                    and 
                    (abs(yarr[j] - yarr[i]) < 0.5 * jobs_data[j][3] + jobs_data[i][3])):

                    ## cosntraints for |xj-xi|
                    x = [vars_map['x'+`j`],vars_map['x'+`i`],vars_map['xp{0},{1}'.format(j,i)],vars_map['xn{0},{1}'.format(j,i)],vars_map['Ix{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                                    
                    self.add(constraint=[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]],sense="E",rhs=0)
                    self.add(constraint=[[x[3],x[4]],[1,-max_t]],sense="L",rhs=0)
                    self.add(constraint=[[x[2],x[4]],[1,max_t]],sense="L",rhs=max_t)
                    self.add(constraint=[[x[2],x[3],x[5]],[1,1,max_t]],sense="G",rhs=0.5*(jobs_data[j][1]+jobs_data[i][1]))

                    ## cosntraints for |yj-yi|
                    x = [vars_map['y'+`j`],vars_map['y'+`i`],vars_map['yp{0},{1}'.format(j,i)],vars_map['yn{0},{1}'.format(j,i)],vars_map['Iy{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                    self.add(constraint=[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]],sense="E",rhs=0)
                    self.add(constraint=[[x[3],x[4]],[1,-number_of_boards]],sense="L",rhs=0)
                    self.add(constraint=[[x[2],x[4]],[1,number_of_boards]],sense="L",rhs=number_of_boards)
                    self.add(constraint=[[x[2],x[3],x[5]],[1,1,-number_of_boards]],sense="G",rhs=0.5*(jobs_data[j][3]+jobs_data[i][3]) - number_of_boards)
                    
                    break # jump for checking the next job                
                

class EmulatorsCutCallback(UserCutCallback):
    # init general UserCut Callback - required by the API for some housekeeping
    def __init__(self, env):
        UserCutCallback.__init__(self, env)

    def __call__(self):
        vars_map = EmulatorsCplexSolverLayout.vars_map
        jobs_data = EmulatorsCplexSolverLayout.jobs_data
        number_of_boards = EmulatorsCplexSolverLayout.number_of_boards
        max_t = EmulatorsCplexSolverLayout.maximum_t_value

        len_jobs = len(jobs_data)
        xarr = [self.get_values(vars_map['x'+`j`]) for j in range(len_jobs)]
        yarr = [self.get_values(vars_map['y'+`j`]) for j in range(len_jobs)]

        for j in range(len_jobs):
            for i in range(len_jobs):
                if j<=i: continue

                if ((abs(xarr[j] - xarr[i]) < 0.5 * (jobs_data[j][1] + jobs_data[i][1])) 
                    and 
                    (abs(yarr[j] - yarr[i]) < 0.5 * jobs_data[j][3] + jobs_data[i][3])):

                    print "{},{} - {}-{}".format(j,i,xarr[j],xarr[i])

                    ## cosntraints for |xj-xi|
                    x = [vars_map['x'+`j`],vars_map['x'+`i`],vars_map['xp{0},{1}'.format(j,i)],vars_map['xn{0},{1}'.format(j,i)],vars_map['Ix{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                                    
                    self.add(cut=[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]],sense="E",rhs=0)
                    self.add(cut=[[x[3],x[4]],[1,-max_t]],sense="L",rhs=0)
                    self.add(cut=[[x[2],x[4]],[1,max_t]],sense="L",rhs=max_t)
                    self.add(cut=[[x[2],x[3],x[5]],[1,1,max_t]],sense="G",rhs=0.5*(jobs_data[j][1]+jobs_data[i][1]))

                    ## cosntraints for |yj-yi|
                    x = [vars_map['y'+`j`],vars_map['y'+`i`],vars_map['yp{0},{1}'.format(j,i)],vars_map['yn{0},{1}'.format(j,i)],vars_map['Iy{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                    self.add(cut=[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]],sense="E",rhs=0)
                    self.add(cut=[[x[3],x[4]],[1,-number_of_boards]],sense="L",rhs=0)
                    self.add(cut=[[x[2],x[4]],[1,number_of_boards]],sense="L",rhs=number_of_boards)
                    self.add(cut=[[x[2],x[3],x[5]],[1,1,-number_of_boards]],sense="G",rhs=0.5*(jobs_data[j][3]+jobs_data[i][3]) - number_of_boards)
                    
                    break # jump for checking the next job                
    

class EmulatorsCplexSolverLayout(object):
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
    penalty_weight = 1000
    tardiness_weight = 1



    @staticmethod
    def clean():
        EmulatorsCplexSolverLayout.jobs_data = []
        EmulatorsCplexSolverLayout.number_of_boards = None
        EmulatorsCplexSolverLayout.current_best_objective = None
        EmulatorsCplexSolverLayout.current_best_penalty = None
        EmulatorsCplexSolverLayout.lazy_constraints = set()
        EmulatorsCplexSolverLayout.lazy_start_objective = None
        EmulatorsCplexSolverLayout.lazy_start_penlaty = None
        EmulatorsCplexSolverLayout.vars_map = dict()
        EmulatorsCplexSolverLayout.register_callbacks = False
        EmulatorsCplexSolverLayout.maximum_t_value = None
        EmulatorsCplexSolverLayout.time_divider = None


    def solve(self):
        """ 
        @type model: Cplex
        """
        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in EmulatorsCplexSolverLayout.jobs_data]
        processtimes = [i[1] for i in EmulatorsCplexSolverLayout.jobs_data]
        duedates = [i[2] for i in EmulatorsCplexSolverLayout.jobs_data]
        sizes = [i[3] for i in EmulatorsCplexSolverLayout.jobs_data]
        readytimes = [i[4] for i in EmulatorsCplexSolverLayout.jobs_data]

        number_of_boards = EmulatorsCplexSolverLayout.number_of_boards
        
        if EmulatorsCplexSolverLayout.maximum_t_value == None:
            EmulatorsCplexSolverLayout.maximum_t_value = common.get_edr_single_machine_max_time(EmulatorsCplexSolverLayout.jobs_data)

            max_t = EmulatorsCplexSolverLayout.maximum_t_value

        #defined constants
        penalty_weight = EmulatorsCplexSolverLayout.penalty_weight
        tardiness_weight = EmulatorsCplexSolverLayout.tardiness_weight

        cplexSolver = cplex.Cplex()
        
        # set the objective to minimize  or maximize
        cplexSolver.objective.set_sense(cplexSolver.objective.sense.minimize)

        # set time limit to 2 hours
        cplexSolver.parameters.timelimit.set(7200)
        
        cplexSolver.parameters.parallel.set(1)
        cplexSolver.parameters.threads.set(4)

        # set node log interval to 10
        cplexSolver.parameters.mip.interval.set(10)

        ############# Add variables  ##################################
        print "Adding variables .. "
        vars_map = EmulatorsCplexSolverLayout.vars_map
        
        # xj variables, middle of processing time
        variable_names = ['x{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('x{0}'.format(j),cplexSolver.variables.get_indices('x{0}'.format(j))) for j in jobs])

        # yj variables, middle of boards size
        variable_names = ['y{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('y{0}'.format(j),cplexSolver.variables.get_indices('y{0}'.format(j))) for j in jobs])

        # cj variables, completion time
        variable_names = ['c{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('c{0}'.format(j),cplexSolver.variables.get_indices('c{0}'.format(j))) for j in jobs])

        # Tj variables, tardiness
        variable_names = ['T{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [tardiness_weight]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('T{0}'.format(j),cplexSolver.variables.get_indices('T{0}'.format(j))) for j in jobs])

        # Uj variables, penalty value
        variable_names = ['U{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [penalty_weight]*len(variable_names), types="B"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('U{0}'.format(j),cplexSolver.variables.get_indices('U{0}'.format(j))) for j in jobs])

        # zij variables, penalty value
        variable_names = ['z{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="B"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('z{0},{1}'.format(j,i),cplexSolver.variables.get_indices('z{0},{1}'.format(j,i))) for j in jobs for i in jobs])

        # absolute values variables for |xi-xj|
        variable_names = ['xp{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('xp{0},{1}'.format(j,i),cplexSolver.variables.get_indices('xp{0},{1}'.format(j,i))) for j in jobs for i in jobs])

        variable_names = ['xn{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('xn{0},{1}'.format(j,i),cplexSolver.variables.get_indices('xn{0},{1}'.format(j,i))) for j in jobs for i in jobs])

        variable_names = ['Ix{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="B"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('Ix{0},{1}'.format(j,i),cplexSolver.variables.get_indices('Ix{0},{1}'.format(j,i))) for j in jobs for i in jobs])


        # absolute values variables for |yi-yj|
        variable_names = ['yp{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('yp{0},{1}'.format(j,i),cplexSolver.variables.get_indices('yp{0},{1}'.format(j,i))) for j in jobs for i in jobs])

        variable_names = ['yn{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('yn{0},{1}'.format(j,i),cplexSolver.variables.get_indices('yn{0},{1}'.format(j,i))) for j in jobs for i in jobs])

        variable_names = ['Iy{0},{1}'.format(j,i) for j in jobs for i in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="B"*len(variable_names),lb=[0]*len(variable_names), names=variable_names)
        vars_map.update([('Iy{0},{1}'.format(j,i),cplexSolver.variables.get_indices('Iy{0},{1}'.format(j,i))) for j in jobs for i in jobs])


        ############# Add Constraints  ##################################
        print "Adding constraints ... "

        ## constraint of whether we need to have penalty for this job
        constraints = [[[vars_map['U'+`j`],vars_map['c'+`j`]],[max_t,-1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[-1*duedates[j] for j in jobs],names=["Up"+`j` for j in jobs])

        ## constraint the completion time variable
        constraints = [[[vars_map['c'+`j`],vars_map['x'+`j`]],[1,-1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="E"*len(constraints),rhs=[0.5*processtimes[j] for j in jobs])

        ## maximum boards constraint
        constraints = [[[vars_map['y'+`j`]],[1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="L"*len(constraints),rhs=[number_of_boards - 0.5 * sizes[j] for j in jobs])

        ## arrival time constraint
        constraints = [[[vars_map['x'+`j`]],[1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[readytimes[j] + 0.5 * processtimes[j] for j in jobs])

        ## boards minimal yj constraint
        constraints = [[[vars_map['y'+`j`]],[1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[0.5 * sizes[j] for j in jobs])

        ## Tardinesss of job j
        constraints = [[[vars_map['T'+`j`],vars_map['c'+`j`]],[1,-1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[-1*duedates[j] for j in jobs])

        ## Absolute value constraints
        for j in jobs:
            for i in jobs:
                if i == j: continue
                ## cosntraints for |xj-xi|
                x = [vars_map['x'+`j`],vars_map['x'+`i`],vars_map['xp{0},{1}'.format(j,i)],vars_map['xn{0},{1}'.format(j,i)],vars_map['Ix{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]]],senses="E",rhs=[0])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[3],x[4]],[1,-max_t]]],senses="L",rhs=[0])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[4]],[1,max_t]]],senses="L",rhs=[max_t])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[3],x[5]],[1,1,max_t]]],senses="G",rhs=[0.5*(processtimes[j]+processtimes[i])])

                ## cosntraints for |yj-yi|
                x = [vars_map['y'+`j`],vars_map['y'+`i`],vars_map['yp{0},{1}'.format(j,i)],vars_map['yn{0},{1}'.format(j,i)],vars_map['Iy{0},{1}'.format(j,i)],vars_map['z{0},{1}'.format(j,i)]]
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[3],x[0],x[1]],[1,-1,-1,1]]],senses="E",rhs=[0])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[3],x[4]],[1,-number_of_boards]]],senses="L",rhs=[0])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[4]],[1,number_of_boards]]],senses="L",rhs=[number_of_boards])
                cplexSolver.linear_constraints.add(lin_expr=[[[x[2],x[3],x[5]],[1,1,-number_of_boards]]],senses="G",rhs=[0.5*(sizes[j]+sizes[i]) - number_of_boards])

        end_preparation = time.time()
        print "Preparation ended, took" + `end_preparation - start_preparation` + " seconds"
        
        cplexSolver.register_callback(EmulatorsCutCallback)
        cplexSolver.register_callback(EmulatorsLazyCallback)
        
        cplexSolver.write("layout.lp")
        start_solve = time.time()
        cplexSolver.solve()
        end_solve = time.time()

        print "Solved in " + `end_solve - start_solve`

        print cplexSolver.solution.get_status()

        result = common.CplexResult()
        # if infeasible
        if cplexSolver.solution.get_status() == 103:
            result.feasible = False
            result.optimal = True
            return result
        if cplexSolver.solution.get_status() == 108:
            result.feasible = False
            result.optimal = False
            return result

        if cplexSolver.solution.get_status() == 107:
            result.feasible = True
            result.optimal = False
        elif cplexSolver.solution.get_status() == 101 or cplexSolver.solution.get_status() == 102:
            result.feasible = True
            result.optimal = True


        jobInfoList = []

        for j in jobs:
            info = common.JobInfo()
            info.job_id = j
            info.start_time = int(round(cplexSolver.solution.get_values(vars_map['x'+`j`]) -  0.5 * processtimes[j]))
            info.first_board = int(round(cplexSolver.solution.get_values(vars_map['y'+`j`]) - 0.5 * sizes[j]))
            info.finish_time = int(round(info.start_time + processtimes[j]))
            info.tardiness = int(round(cplexSolver.solution.get_values(vars_map['T'+`j`])))
            jobInfoList.append(info)

        result.total_penalty = sum([cplexSolver.solution.get_values('U'+`j`) for j in jobs])
        result.total_tardiness = sum([cplexSolver.solution.get_values('T'+`j`) for j in jobs])
        result.objective_value = int(cplexSolver.solution.get_objective_value())
        result.job_info = jobInfoList

        return result

def solve_cplex_only(jobs_data, number_of_boards):
    
    start_time = time.time()
    EmulatorsCplexSolverLayout.clean()
    cplex_sover = EmulatorsCplexSolverLayout()
    EmulatorsCplexSolverLayout.jobs_data = jobs_data
    EmulatorsCplexSolverLayout.number_of_boards = number_of_boards

    cplex_result = cplex_sover.solve()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result

#************* Main Program ************************
if __name__ == "__main__":
    common.solve_and_save(None,"Layout3",solve_cplex_only)