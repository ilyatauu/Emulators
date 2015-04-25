using CP;

tuple Job
{
  key int id;
  int duration;
  int duedate;
  int capacity;
  int available;
};  



//{Job} jobs = {<1,2,1,1,100>,<2,1,2,1,100>,<3,2,2,1,100>,<4,3,1,1,100>};
//{int} Machines = {1,2,3,4};
//{Job} jobs = {<0,1,7,4,0>,<1,2,18,8,0>,<2,4,24,5,0>,<3,6,7,5,0>,<4,5,15,5,0>,<5,5,16,5,0>,<6,3,21,9,0>,<7,10,13,5,0>,<8,7,23,6,0>,<9,2,3,8,0>,<10,4,4,1,0>,<11,2,15,7,0>,<12,5,7,6,0>,<13,5,6,9,0>,<14,7,11,1,0>};
//int M = 15;

//{Job} jobs = {<0,8,21,7,0>,<1,1,13,4,0>,<2,3,5,7,0>,<3,9,9,8,0>,<4,10,20,4,0>,<5,9,16,4,0>,<6,5,22,7,0>,<7,10,15,2,0>,<8,6,12,5,0>,<9,6,25,5,0>,<10,3,7,2,0>,<11,1,7,2,0>,<12,7,12,3,0>,<13,2,8,5,0>,<14,7,16,6,0>};
//int M = 15;
int M = ... ;
{Job} jobs = ...;
{int} Machines = {i | i in 0 .. M-1};

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

dexpr float objValue = 1000 * sum(j in jobs) U[j] + sum(j in jobs) maxl(0,endOf(tijobs[j]) - j.duedate);
dexpr float total_penalty = sum(j in jobs) U[j];
dexpr float total_tardiness = sum(j in jobs) maxl(0,endOf(tijobs[j]) - j.duedate);

execute {
  var p = cp.param;
  p.TimeLimit = 10;
  //p.LogVerbosity = "Quiet";
}  
//minimize objValue;
//minimize objValue;
subject to {
    
  completion_time == max(j in jobs) endOf(tijobs[j]);
  
  //sum(j in jobs) U[j] <= 2;
  startOf(tijobs[<0>]) == 21;
  startOf(tijobs[<1>]) == 31;
  startOf(tijobs[<2>]) == 40;
  presenceOf(tialts[<0,1>]) == 0;
  
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
    	m >= a.smachine && a.smachine+a.job.capacity > m) pulse(tialts[a],1) <= 1;
}

main
{
  thisOplModel.generate();
  
  var result = cp.solve();
  
  writeln(cp.info.FailStatus);
  
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

execute PostProcess{
     
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