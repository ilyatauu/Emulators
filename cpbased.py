import subprocess
import string
import tempfile
import formulations.structures


class CpResult(object):
    objective_value = None
    total_penalty = None
    total_tardiness = None
    optimal = None
    feasible = None
    schedule_completion_time = None
    total_run_time = None
    jobs_results = []


class EmulatorsCpSolver(object):
    # default time limit of 10 seconds
    time_limit = 10

    total_penalty = None
    objective_value = None
    total_penalty_lower_bound = None

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
      Job job;
      key int job_id;
      key int smachine;
    };

    {Alternative2} Alternatives2 =
	    {<j,j.id,m> | j in jobs, m in Machines: j.capacity + m <= card(Machines)};

    dvar interval tialts[a in Alternatives2] optional;
    dvar interval tijobs[j in jobs] size j.duration;

    dvar boolean U[j in jobs]; // penalty if job is not completed on time
    dvar int completion_time;  // last completion time

	// Added to make the solution more tight
    dexpr int total_start_time = sum(j in jobs) (startOf(tijobs[j]));
    dexpr int total_start_board = sum(a in Alternatives2) presenceOf(tialts[a]) * a.smachine;

	// Tardiness plus penalty objective functions
    dexpr int total_penalty = sum(j in jobs) U[j];

    dexpr int total_tardiness = sum(j in jobs) maxl(0,endOf(tijobs[j]) - j.duedate);

	// Objective value
    dexpr int objValue = 10000000 * total_penalty + total_tardiness + total_start_time + total_start_board;

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

	  var startTime = new Date();
      cp.startNewSearch();
      var result = cp.solve();
      cp.endSearch();
      var endTime = new Date();
      var run_time = (endTime - startTime) / 1000.0

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
      writeln("total_run_time:" + run_time + ";");
    }

    execute {
      writeln("objective_value:" + objValue + ";");

      writeln("total_penalty:" + total_penalty + ";");
      writeln("total_tardiness:" + total_tardiness + ";");
      writeln("schedule_completion_time:" + completion_time + ";");

      var j;
      var jobs_array = new Array();
      var alternatives_array = new Array();
      var index = 0;
      for (j in jobs)
      {
        jobs_array[index] = j.id + "," + tijobs[j].start;
        index++;


      }

      index = 0;
      for (var a in Alternatives2)
      {
        if (tialts[a].present == 1)
        {
            alternatives_array[index] = a.job.id + "," + tialts[a].start + "," + a.smachine;
            index++;
        }
      }


      writeln("jobs_result:" + jobs_array.join("|") + ";");
      writeln("alternatives_result:" + alternatives_array.join("|") + ";");
    }
    """

    def get_opl_template_penalty_only(self):
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
      Job job;
      key int job_id;
      key int smachine;
    };  

    {Alternative2} Alternatives2 = 
	    {<j,j.id,m> | j in jobs, m in Machines: j.capacity + m <= card(Machines)};

    dvar interval tialts[a in Alternatives2] optional;
    dvar interval tijobs[j in jobs] size j.duration;

    dvar boolean U[j in jobs]; // penalty if job is not completed on time
    dvar int completion_time;  // last completion time

    dexpr int total_start_time = sum(j in jobs) (startOf(tijobs[j]));
    dexpr int total_start_board = sum(a in Alternatives2) presenceOf(tialts[a]) * a.smachine;
    dexpr int total_penalty = sum(j in jobs) U[j];
    dexpr int objValue = 10000000 * total_penalty + total_start_time + total_start_board;


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
  
      var startTime = new Date();
      cp.startNewSearch();
      var result = cp.solve();
      cp.endSearch();
      var endTime = new Date();
      var run_time = (endTime - startTime) / 1000.0
  
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
      writeln("total_run_time:" + run_time + ";");
    } 

    execute {
      writeln("objective_value:" + objValue + ";");
      writeln("schedule_completion_time:" + completion_time + ";");
      writeln("total_penalty:" + total_penalty + ";");

      var j;
      var jobs_array = new Array();
      var alternatives_array = new Array();
      var index = 0;
      for (j in jobs)
      {
        jobs_array[index] = j.id + "," + tijobs[j].start;
        index++;
      } 
  
      index = 0;
      for (var a in Alternatives2)
      {
        if (tialts[a].present == 1)
        {
            alternatives_array[index] = a.job.id + "," + tialts[a].start + "," + a.smachine;
            index++;
        }
      }

      writeln("jobs_result:" + jobs_array.join("|") + ";");
      writeln("alternatives_result:" + alternatives_array.join("|") + ";");
    }
    """

    def get_opl_model2(self, template_function, job_tuples, number_of_boards, job_constraints=None):
        model = template_function()
        model = model.replace("@number_of_boards", repr(number_of_boards))
        model = model.replace("@jobs_tuples", self.get_job_string_tuples(job_tuples))
        model = model.replace("@time_limit", repr(self.time_limit))

        additional_constraints = ""
        if self.total_penalty is not None:
            additional_constraints = "{}\t\ttotal_penalty <= {};\n\n".format(
                additional_constraints,
                repr(int(self.total_penalty)))
        if self.objective_value is not None:
            additional_constraints = "{}\t\tobjValue <= {};\n\n".format(
                additional_constraints,
                repr(int(self.objective_value)))
        if self.total_penalty_lower_bound is not None:
            additional_constraints = "{}\t\tobjValue >= {};\n\n".format(
                additional_constraints,
                repr(int(self.total_penalty_lower_bound)))

        constraints = self.get_job_constraints(job_constraints)
        additional_constraints = "{}\n\n{}".format(additional_constraints, constraints)
        model = model.replace("<constraints_placeholder>", additional_constraints)

        return model


    def get_opl_model(self, job_tuples, number_of_boards):
        model = self.get_opl_template()
        model = model.replace("@number_of_boards", repr(number_of_boards))
        model = model.replace("@jobs_tuples", self.get_job_string_tuples(job_tuples))
        model = model.replace("@time_limit", repr(self.time_limit))

        additional_constraints = ""
        if self.total_penalty is not None:
            additional_constraints = "{}\t\ttotal_penalty <= {};\n\n".format(
                additional_constraints, repr(int(self.total_penalty)))
        if self.objective_value is not None:
            additional_constraints = "{}\t\tobjValue <= {};\n\n".format(
                additional_constraints, repr(int(self.objective_value)))

        model = model.replace("<constraints_placeholder>", additional_constraints)

        return model

    def get_opl_model_penalty(self, job_tuples, number_of_boards, job_constraints=None):
        model = self.get_opl_template_penalty_only()
        model = model.replace("@number_of_boards", repr(number_of_boards))
        model = model.replace("@jobs_tuples", self.get_job_string_tuples(job_tuples))
        model = model.replace("@time_limit", repr(self.time_limit))

        additional_constraints = ""
        if self.total_penalty is not None:
            additional_constraints = "{}\t\ttotal_penalty <= {};\n\n".format(
                additional_constraints,
                repr(int(self.total_penalty)))
        if self.objective_value is not None:
            additional_constraints = "{}\t\tobjValue <= {};\n\n".format(
                additional_constraints,
                repr(int(self.objective_value)))
        if self.total_penalty_lower_bound is not None:
            additional_constraints = "{}\t\tobjValue >= {};\n\n".format(
                additional_constraints,
                repr(int(self.total_penalty_lower_bound)))

        constraints = self.get_job_constraints(job_constraints)
        additional_constraints = "{}\n\n{}".format(additional_constraints, constraints)
        model = model.replace("<constraints_placeholder>", additional_constraints)

        return model

    def get_job_constraints(self, job_constraints):
        if job_constraints is None:
            return ""

        constraints = []
        constraints.extend(["startOf(tijobs[<{}>]) == {};".format(c.job_id, c.start_time)
                            for c in job_constraints if c.start_time is not None])

        constraints.extend(["endOf(tijobs[<{}>]) <= {};".format(c.job_id, c.duedate)
                           for c in job_constraints if c.duedate is not None])

        constraints.extend(["presenceOf(tialts[<{},{}>]) == 1;".format(c.job_id, c.first_board)
                           for c in job_constraints if c.first_board is not None])

        return string.join(constraints, "\n")

    def get_tuple_string(self, jobid, processtime, duedate, size, available):
        return "<{0},{1},{2},{3},{4}>".format(jobid, processtime, duedate, size, available)

    def get_job_string_tuples(self, job_tuples):
        return "{{{0}}}".format(",".join(
            map(lambda j: self.get_tuple_string(j[0], j[1], j[2], j[3], j[4]), job_tuples)))

    def get_value(self, longstring, key):
        index = string.find(longstring, key)

        if index == -1:
            return None

        value = string.replace(longstring[index:string.find(longstring, ";", index)], key + ":", "")

        return value

    def get_array_value(self, longstring, key):
        line = self.get_value(longstring, key)
        values = line.split("|")
        return [v.split(",") for v in values]

    def solve(self, jobs_data, number_of_boards, job_constraints=None):
        opl_model = self.get_opl_model2(
            self.get_opl_template, jobs_data, number_of_boards, job_constraints)

        # Create temporary files to use with oplrun command
        tmp_file = tempfile.NamedTemporaryFile(suffix=".mod", delete=False)
        tmp_stdout = tempfile.NamedTemporaryFile(delete=False)

        print "Temporary file created: " + tmp_file.name
        print "Temporary file created: " + tmp_stdout.name

        tmp_file.write(opl_model)
        tmp_file.close()

        subprocess.call(["oplrun", tmp_file.name], stdout=tmp_stdout)
        tmp_stdout.close()

        tmp_stdout = open(tmp_stdout.name, 'rb')
        oplrun_result = tmp_stdout.read()
        tmp_stdout.close()

        cp_result = CpResult()
        cp_result.feasible = self.get_value(oplrun_result, "feasible") == "true"

        if cp_result.feasible is False:
            return cp_result

        cp_result.optimal = self.get_value(oplrun_result, "optimal") == "true"
        cp_result.objective_value = int(self.get_value(oplrun_result, "objective_value"))
        cp_result.total_penalty = int(self.get_value(oplrun_result, "total_penalty"))
        cp_result.total_run_time = float(self.get_value(oplrun_result, "total_run_time"))
        cp_result.total_tardiness = int(self.get_value(oplrun_result, "total_tardiness"))
        cp_result.schedule_completion_time = int(self.get_value(oplrun_result, "schedule_completion_time"))
        # cp_result.jobs_results = [[int(x[0]), int(x[1])] for x in self.get_array_value(oplrun_result, "jobs_result")]
        cp_result.jobs_results = [[int(x[0]), int(x[1]), int(x[2])]
                                  for x in self.get_array_value(oplrun_result, "alternatives_result")]

        return cp_result

    def solve_penalty_only(self, jobs_data, number_of_boards, job_constraints=None):
        opl_model = self.get_opl_model2(
            self.get_opl_template_penalty_only, jobs_data, number_of_boards, job_constraints)

        # Create temporary files to use with oplrun command
        tmp_file = tempfile.NamedTemporaryFile(suffix=".mod", delete=False)
        tmp_stdout = tempfile.NamedTemporaryFile(delete=False)

        print "Temporary file created: " + tmp_file.name
        print "Temporary file created: " + tmp_stdout.name

        tmp_file.write(opl_model)
        tmp_file.close()

        subprocess.call(["oplrun", tmp_file.name], stdout=tmp_stdout)
        tmp_stdout.close()

        tmp_stdout = open(tmp_stdout.name, 'rb')
        oplrun_result = tmp_stdout.read()
        tmp_stdout.close()

        cp_result = CpResult()
        cp_result.feasible = self.get_value(oplrun_result, "feasible") == "true"

        if cp_result.feasible is False:
            return cp_result

        cp_result.optimal = self.get_value(oplrun_result, "optimal") == "true"
        cp_result.objective_value = int(self.get_value(oplrun_result, "objective_value"))
        cp_result.total_penalty = int(self.get_value(oplrun_result, "total_penalty"))
        cp_result.total_run_time = float(self.get_value(oplrun_result, "total_run_time"))
        cp_result.schedule_completion_time = int(self.get_value(oplrun_result, "schedule_completion_time"))
        # cp_result.jobs_results = [[int(x[0]), int(x[1])] for x in self.get_array_value(oplrun_result, "jobs_result")]
        cp_result.jobs_results = [[int(x[0]), int(x[1]), int(x[2])]
                                  for x in self.get_array_value(oplrun_result, "alternatives_result")]

        return cp_result
