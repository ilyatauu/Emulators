import time
import cplex
from cplex.callbacks import LazyConstraintCallback, UserCutCallback
import threading
import math
import csv
import fileinput
import subprocess
import tempfile
import string
import sys
import random

class CpResult(object):

    objective_value = None;
    total_penalty = None;
    total_tardiness = None;
    optimal = None;
    feasible = None;
    schedule_completion_time = None;
    jobs_results = []

# This class uses oplrun commadline tool to run emulators opl model.
# It assumes that oplrun is known in the envrionment
class EmulatorsCpSolver(object):

    # default time limit of 10 seconds
    time_limit = 10
    total_penalty = None
    objective_value = None
    satisfability = False
    
    # list of tuples (jobid, job start time)
    time_start_constraints = []

    # list of tuples (jobid, starting board)
    machine_start_constraints = []


    def get_opl_template(self):
        return """
    using CP;

    tuple Job
    {
      key int id;
      int duration;
      int duedate;
      int capacity;
      int available;
    };  

    int M = @number_of_boards;
    {int} Machines = {i | i in 0 .. M-1};
    {Job} jobs = @jobs_tuples;

    tuple Alternative2
    {
      key int id;
      Job job;
      key int smachine;
    };  

    {Alternative2} Alternatives2 = 
	    {<j.id,j,m> | j in jobs, m in Machines: j.capacity + m <= card(Machines)};

    dvar interval tialts[a in Alternatives2] optional;
    dvar interval tijobs[j in jobs] size j.duration;

    dvar boolean U[j in jobs]; // penalty if job is not completed on time
    dvar int completion_time;  // last completion time

    dexpr int total_penalty = sum(j in jobs) U[j];
    dexpr int total_tardiness = sum(j in jobs) maxl(0,endOf(tijobs[j]) - j.duedate);
    dexpr int objValue = 1000 * total_penalty + total_tardiness;

    execute {
      var p = cp.param;
      p.timeLimit = @time_limit;
      p.LogVerbosity = "Quiet";
    } 

    minimize objValue;

    subject to {

<constraints_placeholder>

      completion_time == max(j in jobs) endOf(tijobs[j]);

      forall (j in jobs)
        startOf(tijobs[j]) >= j.available;
   
      forall (j in jobs)
      {
	    endOf(tijobs[j]) > j.duedate => U[j] == 1;
	    endOf(tijobs[j]) <= j.duedate => U[j] ==0;   	 	
      }
  
      // only one alternative can happen for each job
      forall (j in jobs)
        alternative(tijobs[j],all(a in Alternatives2: a.job.id == j.id) tialts[a]);
     
      // capacity constraint for all machines	
      forall (m in Machines)
        sum(a in Alternatives2: 
    	    m >=a.smachine && a.smachine+a.job.capacity > m) pulse(tialts[a],1) <= 1;
    };

    main
    {
      thisOplModel.generate();
  
      cp.startNewSearch();
      var result = cp.solve();
      cp.endSearch();
  
      if (cp.info.FailStatus == 13)
      {
        writeln("optimal:true;");
      }
      else
      {
        writeln("optimal:false;");
      }      

      if (result)
      {
        writeln("feasible:true;");
    
        thisOplModel.postProcess();
      }   
      else
      {
        writeln("feasible:false;");
      } 
    } 

    execute {
      writeln("objective_value:" + objValue + ";");
      writeln("total_penalty:" + total_penalty + ";");
      writeln("total_tardiness:" + total_tardiness + ";");
      writeln("schedule_completion_time:" + completion_time + ";");

      var j;
      var jobs_array = new Array();
      for (j in jobs)
      {
        jobs_array[j.id] = j.id + "," + tijobs[j].start;
      } 
  
      writeln("jobs_result:" + jobs_array.join("|") + ";"); 
    }
    """

    def get_opl_model(self,job_tuples, number_of_boards):
        model = self.get_opl_template()
        model = model.replace("@number_of_boards",`number_of_boards`)
        model = model.replace("@jobs_tuples",self.get_job_string_tuples(job_tuples))
        model = model.replace("@time_limit",`self.time_limit`)

        additional_constraints = ""
        if self.total_penalty != None:
            additional_constraints = additional_constraints +  "\t\ttotal_penalty <= " + `int(self.total_penalty)` + ";\n\n"
        if self.objective_value != None:
            additional_constraints = additional_constraints +  "\t\tobjValue <= " + `int(self.objective_value)` + ";\n\n"
        for ct in self.time_start_constraints:
            additional_constraints = additional_constraints + "\t\tstartOf(tijobs[<{}>]) == {};\n\n".format(ct[0],ct[1])
        for cm in self.machine_start_constraints:
            additional_constraints = additional_constraints + "\t\tpresenceOf(tialts[<{},{}>]) == 1;\n\n".format(cm[0],cm[1])

        model = model.replace("<constraints_placeholder>",additional_constraints)

        if self.satisfability == True:
            model = model.replace("minimize objValue;","")

        return model

    def get_tuple_string(self,id, processtime, duedate, size, available):
        return "<{0},{1},{2},{3},{4}>".format(id,processtime, duedate,size,available)

    def get_job_string_tuples(self,job_tuples):
        return "{{{0}}}".format(",".join(map(lambda j: self.get_tuple_string(j[0],j[1],j[2],j[3],j[4]),job_tuples)))

    def get_value(self,longstring, key):
        index = string.find(longstring,key)

        if (index == -1):
            return None

        value = string.replace(longstring[index:string.find(longstring,";",index)],key + ":","")

        return value

    def get_array_value(self, longstring,key):
        line = self.get_value(longstring,key)
        values = line.split("|")
        return [v.split(",") for v in values]

    def solve(self,jobs_data, number_of_boards):
        opl_model = self.get_opl_model(jobs_data,number_of_boards)

        # Create temporary files to use with oplrun command
        tmp_file = tempfile.NamedTemporaryFile(suffix = ".mod", delete = False)
        tmp_stdout = tempfile.NamedTemporaryFile(delete = False)

        print "Temporary file created: " + tmp_file.name
        print "Temporary file created: " + tmp_stdout.name

        tmp_file.write(opl_model)
        tmp_file.close();

        subprocess.call(["oplrun", tmp_file.name], stdout = tmp_stdout)
        tmp_stdout.seek(0)
        oplrun_result = tmp_stdout.read()
        tmp_stdout.close()

        cp_result = CpResult()
        cp_result.feasible = self.get_value(oplrun_result,"feasible") == "true";
        
        if cp_result.feasible == False:
            return cp_result

        cp_result.optimal = self.get_value(oplrun_result, "optimal") == "true";
        cp_result.objective_value = int(self.get_value(oplrun_result,"objective_value"))
        cp_result.total_penalty  = int(self.get_value(oplrun_result, "total_penalty"))
        cp_result.total_tardiness = int(self.get_value(oplrun_result,"total_tardiness"))
        cp_result.schedule_completion_time = int(self.get_value(oplrun_result,"schedule_completion_time"))
        cp_result.jobs_results = [[int(x[0]),int(x[1])] for x in self.get_array_value(oplrun_result,"jobs_result")]

        return cp_result

class EmulatorsCplexData(object):
    jobs_data = []
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

    @staticmethod
    def clean():
        EmulatorsCplexData.jobs_data = []
        EmulatorsCplexData.number_of_boards = None
        EmulatorsCplexData.current_best_objective = None
        EmulatorsCplexData.current_best_penalty = None
        EmulatorsCplexData.lazy_constraints = set()
        EmulatorsCplexData.lazy_start_objective = None
        EmulatorsCplexData.lazy_start_penlaty = None
        EmulatorsCplexData.vars_map = dict()
        EmulatorsCplexData.register_callbacks = False
        EmulatorsCplexData.maximum_t_value = None
        EmulatorsCplexData.time_divider = None

class JobInfo(object):
    job_id = None
    start_time = None
    finish_time = None
    first_board = None
    tardiness = None

class CplexResult(object):
    feasible = None
    optimal = None
    objective_value = None
    total_penalty = None
    total_tardiness = None
    job_info = []
    total_solve_time = None
    
class EmulatorsLazyCallback(LazyConstraintCallback):

    def __call__(self):
        
        ## We will use this to make the callback threadsafe
        lock = threading.Lock()
        jobs = [i[0] for i in EmulatorsCplexData.jobs_data]
        total_penalty = round(sum([self.get_values('U'+`j`) for j in jobs]))
        objective_value = self.get_objective_value()
        
        print "MIP Solution, objective: {0}; total_penalty: {1}".format(objective_value,total_penalty)

        # start thread safe block (inside try .. finally)
        try:
            lock.acquire()
            print "EmulatorsCplexData.lazy_start_objective = " + `EmulatorsCplexData.lazy_start_objective`
            print "objective_value = " + `objective_value`
            if EmulatorsCplexData.lazy_start_objective != None and EmulatorsCplexData.lazy_start_objective <= round(objective_value):
                print "Lazy call back, have nothing to do"
                return
        finally:
            # end of thread safe block
            lock.release()

        solver = EmulatorsCpSolver()
        solver.total_penalty = total_penalty
        solver.objective_value = objective_value
        solver.time_limit = 3
        cp_result = solver.solve(EmulatorsCplexData.jobs_data, EmulatorsCplexData.number_of_boards)

        if cp_result.feasible == False:
            "CP Did not find any feasible solution"
            return

        print "CpSolution: penalty:" + `cp_result.total_penalty` + "; objective: " + `cp_result.objective_value`

        penalty_id = "p" + `cp_result.total_penalty`
        objective_id = "o" + `cp_result.objective_value`

        # start thread safe block
        # start thread safe block (inside try .. finally)
        try:
            lock.acquire()

            objecttive_exists = objective_id in EmulatorsCplexData.lazy_constraints
            penalty_exsits = penalty_id in EmulatorsCplexData.lazy_constraints
            
            if EmulatorsCplexData.lazy_start_objective == None or EmulatorsCplexData.lazy_start_objective >= cp_result.objective_value:
                EmulatorsCplexData.lazy_start_objective = int(round(cp_result.objective_value))
                EmulatorsCplexData.lazy_start_penlaty = int(round(cp_result.total_penalty))
                EmulatorsCplexData.current_best_objective = EmulatorsCplexData.lazy_start_objective
                EmulatorsCplexData.current_best_penalty = EmulatorsCplexData.lazy_start_penlaty

            if penalty_exsits == False:
                print "adding constraint " + penalty_id
                EmulatorsCplexData.lazy_constraints.add(penalty_id)
                # add late jobs constraints
                self.add(constraint=[['U'+`j` for j in jobs],[1]*len(jobs)],sense="L",rhs=int(cp_result.total_penalty))

            if objective_id not in EmulatorsCplexData.lazy_constraints:
                EmulatorsCplexData.lazy_constraints.add(objective_id)
                print "adding constraint " + objective_id
                # add objective value constraint
                self.add(constraint=[['U'+`j` for j in jobs] + ['T' + `j` for j in jobs],[1000]*len(jobs) + [1]*len(jobs)],sense="L",rhs=int(cp_result.objective_value))
        finally:
            # end of thread safe block
            lock.release()

class EmulatorsCutCallback(UserCutCallback):

    last_ten_bad_cuts = []

    # init general UserCut Callback - required by the API for some housekeeping
    def __init__(self, env):
        UserCutCallback.__init__(self, env)

    def __call__(self):
        
        vars_map = EmulatorsCplexData.vars_map 
        jobs_data = EmulatorsCplexData.jobs_data
        boards = EmulatorsCplexData.number_of_boards
        max_t = EmulatorsCplexData.maximum_t_value
        
        
        vars = [((j,m,t), vars_map['x{0},{1},{2}'.format(j,m,t)], self.get_values(vars_map['x{0},{1},{2}'.format(j,m,t)])) for j,m,t in 
                    [(random.randint(0,len(jobs_data)-1),random.randint(0,boards-1),random.randint(0,max_t-1)) for k in range(100)]]
        
        vars = sorted(vars,key=lambda x: x[2],reverse=True)
        
        sum = 0
        scut = []
        time_start_constraints = []
        machine_start_constraints = []
        for r in range(1,len(vars)+1):
            if sum + vars[r-1][2] > r-1:
                sum += vars[r-1][2]
                time_start_constraints.append((vars[r-1][0][0],vars[r-1][0][2]))
                machine_start_constraints.append((vars[r-1][0][0],vars[r-1][0][1]))
                scut.append(vars[r-1][1])
            else:
                break
        
        r = r-1

        if r < math.ceil(len(jobs_data)*0.5):
            return
        
        # check if we already has result for this
        for k in EmulatorsCutCallback.last_ten_bad_cuts:
            if cmp(k,vars[0:r]) == 0:
                return

        solver = EmulatorsCpSolver()
        solver.total_penalty = EmulatorsCplexData.current_best_penalty

        solver.time_start_constraints = time_start_constraints
        solver.machine_start_constraints = machine_start_constraints
        solver.time_limit = 2
        solver.satisfability = True
        cp_result = solver.solve(jobs_data, boards)

        # we found a separating cut
        if cp_result.feasible == False and cp_result.optimal == True:
            print "adding cut"
            self.add(cut=[scut,1*len(scut)],sense="L",rhs=r-1)
        else:
            if len(EmulatorsCutCallback.last_ten_bad_cuts) == 10:
                del EmulatorsCutCallback.last_ten_bad_cuts[0]

            EmulatorsCutCallback.last_ten_bad_cuts.append(sorted([x[1] for x in vars[0:r]]))
  
class EmulatorsCplexSolver(object):
    """description of class"""

    def solve(self):

        print "start preparation"

        start_preparation = time.time()
        jobs = [i[0] for i in EmulatorsCplexData.jobs_data]
        processtimes = [i[1] for i in EmulatorsCplexData.jobs_data]
        duedates = [i[2] for i in EmulatorsCplexData.jobs_data]
        sizes = [i[3] for i in EmulatorsCplexData.jobs_data]
        readytimes = [i[4] for i in EmulatorsCplexData.jobs_data]

        machines = EmulatorsCplexData.number_of_boards
        if EmulatorsCplexData.maximum_t_value == None:
            EmulatorsCplexData.maximum_t_value = get_edr_single_machine_max_time(EmulatorsCplexData.jobs_data)
        
        MaxTime = EmulatorsCplexData.maximum_t_value

        print "MaxTime:" + `MaxTime`

        #defined constants
        penalty_weight = 1000
        tardiness_weight = 1

        cplexSolver = cplex.Cplex()
        
        # set the objective to minimize  or maximize
        cplexSolver.objective.set_sense(cplexSolver.objective.sense.minimize)

        # set time limit to 2 hours
        cplexSolver.parameters.timelimit.set(7200)
        
        cplexSolver.parameters.parallel.set(1)
        cplexSolver.parameters.threads.set(4)

        
        # set node log interval to 10
        cplexSolver.parameters.mip.interval.set(10)

        variables_objectives = []
        variables_names = []
        variables_types = []


        ############# Add variables  ##################################
        print "Adding variables .. "
    
        # Xi,j,t variable
        variable_names = ['x{0},{1},{2}'.format(j,m,t) for j in jobs for m in range(machines) for t in range(MaxTime)]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="B"*len(variable_names), names=variable_names)
        
        EmulatorsCplexData.vars_map.update([('x{0},{1},{2}'.format(j,m,t),cplexSolver.variables.get_indices('x{0},{1},{2}'.format(j,m,t))) for j in jobs for m in range(machines) for t in range(MaxTime)])
        
         
         # Uj variables
        variable_names = ['U{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [penalty_weight]*len(variable_names), types="B"*len(variable_names), names=variable_names)
        EmulatorsCplexData.vars_map.update([('U{0}'.format(j),cplexSolver.variables.get_indices('U{0}'.format(j))) for j in jobs])

        # c_j variables
        variable_names = ['c{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [0]*len(variable_names), types="C"*len(variable_names), names=variable_names)
        EmulatorsCplexData.vars_map.update([('c{0}'.format(j),cplexSolver.variables.get_indices('c{0}'.format(j))) for j in jobs])
        
        # Tj variables
        variable_names = ['T{0}'.format(j) for j in jobs]
        cplexSolver.variables.add(obj = [tardiness_weight]*len(variable_names), types="C"*len(variable_names), names=variable_names,lb=[0]*len(variable_names))
        EmulatorsCplexData.vars_map.update([('T{0}'.format(j),cplexSolver.variables.get_indices('T{0}'.format(j))) for j in jobs])
        
        ############# Add Constraints  ##################################
        print "Adding constraints ... "

        ## Add upper bound constraints
        if EmulatorsCplexData.current_best_objective != None:
            EmulatorsCplexData.lazy_constraints.add("o" + `EmulatorsCplexData.current_best_objective`)
            cplexSolver.linear_constraints.add(lin_expr=[[['U'+`j` for j in jobs] + ['T' + `j` for j in jobs],[1000]*len(jobs) + [1]*len(jobs)]],senses=["L"],rhs=[int(EmulatorsCplexData.current_best_objective)])
        
        if EmulatorsCplexData.current_best_penalty != None:
            EmulatorsCplexData.lazy_constraints.add("o" + `EmulatorsCplexData.current_best_penalty`)
            cplexSolver.linear_constraints.add(lin_expr=[[['U'+`j` for j in jobs],[1]*len(jobs)]],senses=["L"],rhs=[int(EmulatorsCplexData.current_best_penalty)])

        ## Every job must run once
        constraints = [[v,[1]*len(v)] for j in jobs for v in [[EmulatorsCplexData.vars_map['x{0},{1},{2}'.format(j,m,t)] for m in range(machines) for t in range(MaxTime)]]]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="E"*len(constraints),rhs=[1]*len(constraints))

        ## On each board at each time t, only one job can run
        start_time = time.time()
        constraints = []
        constraint_v = []
        for m in range(machines):
            for t in range(MaxTime):
                for jj in jobs:
                    for mm in range(max(0,m-sizes[jj]+1), m+1):
                        for tt in range(max(0,t-processtimes[jj]+1),t+1):
                            constraint_v.append(EmulatorsCplexData.vars_map['x{0},{1},{2}'.format(jj,mm,tt)])

                cplexSolver.linear_constraints.add(lin_expr=[[constraint_v,[1]*len(constraint_v)]],senses="L",rhs=[1],names=["m:{0};t:{1}".format(m,t)])
                constraint_v = []
        end_time = time.time()
        print end_time - start_time
        
        ### Prepare other constraints
        sum_over_xjmt_ind = []
        sum_over_xjmt_val_m = []
        sum_over_xjmt_val_t = []

        for j in jobs:
            constraint_v = []
            for m in range(machines):
                for t in range(MaxTime):
                    sum_over_xjmt_ind.append(EmulatorsCplexData.vars_map['x{0},{1},{2}'.format(j,m,t)])
                    sum_over_xjmt_val_m.append(m)
                    sum_over_xjmt_val_t.append(t)
                    
            # add board start constraint
            cplexSolver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind,sum_over_xjmt_val_m]],senses="L",rhs=[machines-sizes[j]],names=["bstart(j:{0})".format(j)])
            # add readiness constraint
            cplexSolver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind,sum_over_xjmt_val_t]],senses="G",rhs=[readytimes[j]],names=["readiness(j:{0})".format(j)])
            # add completion time constraint
            sum_over_xjmt_ind.append(cplexSolver.variables.get_indices('c'+`j`))
            sum_over_xjmt_val_t.append(-1)
            cplexSolver.linear_constraints.add(lin_expr=[[sum_over_xjmt_ind,sum_over_xjmt_val_t]],senses="E",rhs=[-1*processtimes[j]],names=["completion(j:{0})".format(j)])
            # reset lists
            sum_over_xjmt_ind = []
            sum_over_xjmt_val_m = []
            sum_over_xjmt_val_t = []
        
        ## constraint of whether we need to have penalty for this job
        constraints = [[[EmulatorsCplexData.vars_map['U'+`j`],EmulatorsCplexData.vars_map['T'+`j`]],[MaxTime,-1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[0]*len(jobs),names=["Up"+`j` for j in jobs])

        ## Tardinesss of job j
        constraints = [[[EmulatorsCplexData.vars_map['T'+`j`],EmulatorsCplexData.vars_map['c'+`j`]],[1,-1]] for j in jobs]
        cplexSolver.linear_constraints.add(lin_expr=constraints,senses="G"*len(constraints),rhs=[-1*duedates[j] for j in jobs])
       
        
        if EmulatorsCplexData.register_callbacks == True:
            cplexSolver.register_callback(EmulatorsLazyCallback)
            # do not register user cut as it makes things worse, because of cp slow performacne, and big amount of variables
            #cplexSolver.register_callback(EmulatorsCutCallback)

        end_preparation = time.time()
        print "Preparation ended, took" + `end_preparation - start_preparation` + " seconds"
        
        start_solve = time.time()
        cplexSolver.solve()
        end_solve = time.time()

        print "Solved in " + `end_solve - start_solve` 

        print cplexSolver.solution.get_status()

        result = CplexResult()
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
        # update divider if there was any
        if EmulatorsCplexData.time_divider != None:
            div = EmulatorsCplexData.time_divider
        else:
            div = 1

        for j in jobs:
            for m in range(machines):
                for t in range(MaxTime):
                    if cplexSolver.solution.get_values(EmulatorsCplexData.vars_map['x{0},{1},{2}'.format(j,m,t)]) >= 1 - 1e-06:
                        info = JobInfo()
                        info.job_id = j
                        info.start_time = int(math.floor(t * div))
                        info.finish_time =  info.start_time + int(math.floor(processtimes[j] * div))
                        info.tardiness = int(math.floor(cplexSolver.solution.get_values('T'+`j`) * div))
                        info.first_board = m
                        jobInfoList.append(info)

        result.total_penalty = sum([cplexSolver.solution.get_values('U'+`j`) for j in jobs])
        result.total_tardiness = sum([cplexSolver.solution.get_values('T'+`j`) for j in jobs])
        result.objective_value = cplexSolver.solution.get_objective_value()
        result.job_info = jobInfoList

        return result

def load(filename):
    if filename is not None:
        #read csv file
     with open(filename, 'rb') as csvfile:
       data = list(csv.reader(csvfile, delimiter=','))
       # convert to int
       for row in data:
           for i in range(len(row)):
               if row[i] is not '':
                  row[i] = int(row[i])
    return data

def get_output_string(cplex_result):
    """ Create csv string output in format
        jobid, starttime, first_board, tardiness

        if there is no solution, a line:
        -1,-1,-1,-1
        will be returned
    """
    
    if cplex_result.feasible == False:
        return "-1,-1,-1,-1"

    output =  ["{0},{1},{2},{3}".format(i.job_id,i.start_time,i.first_board,i.tardiness) for i in cplex_result.job_info]
    return '\n'.join(output)

def get_edr_single_machine_max_time(jobs_data):
    
    max_time = 0
    for j in jobs_data:
        max_time += j[1] + j[4]
    
    return max_time

def solve_cplex_only(jobs_data, number_of_boards):
    
    start_time = time.time()
    EmulatorsCplexData.clean()
    cplex_sover = EmulatorsCplexSolver()
    EmulatorsCplexData.jobs_data = jobs_data
    EmulatorsCplexData.number_of_boards = number_of_boards

    cplex_result = cplex_sover.solve()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time

    return cplex_result

def solve_cplex_combined(jobs_data, number_of_boards):
    
    start_time = time.time()
    EmulatorsCplexData.clean()
    cplex_sover = EmulatorsCplexSolver()
    EmulatorsCplexData.jobs_data = jobs_data
    EmulatorsCplexData.number_of_boards = number_of_boards
    # Use CP for upper bounds calculation
    cp_solver = EmulatorsCpSolver()
    cp_result = cp_solver.solve(EmulatorsCplexData.jobs_data, EmulatorsCplexData.number_of_boards)
    EmulatorsCplexData.register_callbacks = True

    if cp_result.feasible:    
        EmulatorsCplexData.current_best_penalty = cp_result.total_penalty
        EmulatorsCplexData.current_best_objective = cp_result.objective_value
        if cp_result.total_penalty > 0:
            edr_ordered = sorted(jobs_data,key=lambda x: x[1]+x[4],reverse=True)[0:cp_result.total_penalty]
            tardy_jobs = filter(lambda x: (x[1] + jobs_data[x[0]][1]) > jobs_data[x[0]][2], cp_result.jobs_results)
            EmulatorsCplexData.maximum_t_value = cp_result.schedule_completion_time - sum([jobs_data[x[0]][1] for x in tardy_jobs]) + sum([x[1] for x in edr_ordered]) + max([x[4] for x in edr_ordered])


        print "CP MaxT: " + `EmulatorsCplexData.maximum_t_value`
        print "CP Upper bound total_penalty: " + `cp_result.total_penalty`
        print "CP Upper bound objective value: " + `cp_result.objective_value`
    else:
        EmulatorsCplexData.maximum_t_value = get_edr_single_machine_max_time(EmulatorsCplexData.jobs_data)
    
    max_number = 8000.0
    t_div = max_number / (number_of_boards * len(jobs_data))
    print "T_div = " + `t_div`
    if EmulatorsCplexData.maximum_t_value > t_div:
        div = EmulatorsCplexData.maximum_t_value / t_div
        new_jobs_data = [[x[0],int(math.ceil(x[1] / div)), int(math.ceil(x[2] / div)),x[3],int(math.ceil(x[4] / div))]  for x in EmulatorsCplexData.jobs_data]
        print jobs_data
        print "**********************"
        print new_jobs_data
        EmulatorsCplexData.jobs_data = new_jobs_data
        EmulatorsCplexData.time_divider = div
        EmulatorsCplexData.current_best_penalty = None
        EmulatorsCplexData.current_best_objective = None
        EmulatorsCplexData.maximum_t_value = int(math.ceil(EmulatorsCplexData.maximum_t_value / div))
        print "Time discretization was made with divider of: " + `div`

    cplex_result = cplex_sover.solve()
    end_time = time.time()
    cplex_result.total_solve_time = end_time - start_time
    
    return cplex_result


#************* Main Program ************************
if len(sys.argv) < 2:
    print 'Please enter the full name of the desired file (with extension) at the prompt below'
    #Raw_input is used to collect data from the user
    file = raw_input('> ')
else:
    file = sys.argv[1]
#returns data from the file as a matrix (int format)
data = load(file);

#data related to jobs is starting from the second row in the matrix
jobs_data = []
for i in range(1,len(data)):
    jobs_data.append(data[i]);

cplex_result = solve_cplex_combined(jobs_data,data[0][0])

print "total solve time: " + `cplex_result.total_solve_time`
print "Objective value: " + `cplex_result.objective_value`
print get_output_string(cplex_result)

# wirte results to file
outf = open(file + ".out","w")
outf.writelines(get_output_string(cplex_result))
outf.close()