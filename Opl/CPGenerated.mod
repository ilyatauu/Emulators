
    using CP;

    tuple Job
    {
      key int id;
      int duration;
      int duedate;
      int capacity;
      int available;
    };  

    int M = 8;
    {int} Machines = {i | i in 0 .. M-1};
    {Job} jobs = {<0,9,11,3,0>,<1,2,4,8,0>,<2,7,19,3,0>,<3,1,2,5,0>,<4,4,12,3,0>};

    tuple Alternative2
    {
      Job job;
      int smachine;
    };  

    {Alternative2} Alternatives2 = 
	    {<j,m> | j in jobs, m in Machines: j.capacity + m <= card(Machines)};

    dvar interval tialts[a in Alternatives2] optional;
    dvar interval tijobs[j in jobs] size j.duration;

    dvar boolean U[j in jobs]; // penalty if job is not completed on time
    dvar int completion_time;  // last completion time

    dexpr int objValue = sum(j in jobs) U[j];;

    execute {
      var p = cp.param;
      p.timeLimit = 600;
      p.LogVerbosity = "Quiet";
    }  
    minimize objValue;

    subject to {

		objValue >= 0;



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

      var j;
      var jobs_array = new Array();
      for (j in jobs)
      {
        jobs_array[j.id] = j.id + "," + tijobs[j].start;
      } 
  
      writeln("jobs_result:" + jobs_array.join("|") + ";"); 
    }
    