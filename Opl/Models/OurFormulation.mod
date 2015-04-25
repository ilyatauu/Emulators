 {int} jobs = ...; // jobs
 int M = ...;
  
 // boards that we have 
 
 int p[jobs] = ...; // process time
 int d[jobs] = ...; // job due date
 int s[jobs] = ...; // size of a job
 int a[jobs] = ...; // arrival time of a job
 
int T = max(j in jobs)p[j] * card(jobs);

range time = 0 .. T; // time index the last number is actually T
range machines = 0..M-1;
 
 dvar boolean x[jobs][machines][time];
 dvar boolean U[jobs];
 
 dvar float c[jobs];
 dvar float Tardiness[jobs];
 dvar float objValue; 
 

 minimize objValue;
 subject to
 {
   objValue == sum(j in jobs) 1000 * U[j] + sum(j in jobs) Tardiness[j];
   
   //objValue == sum(j in jobs) Tardiness[j];
   //objValue == sum(j in jobs) U[j];
   
 	//forall (j in jobs) sum(m in machines,t in time : em[j][m]==1) x[j][m][t] == 1;
 	
 	forall (j in jobs) sum(m in machines,t in time) x[j][m][t] == 1;
 		 					
 	forall (m in machines, t in time)
 	  sum(jj in jobs, mm in maxl(0,m-s[jj]+1)..m, tt in maxl(0,t-p[jj]+1)..t) x[jj][mm][tt] <= 1;
 	
 	forall (j in jobs) sum(m in machines, t in time) m * x[j][m][t] <= card(machines) - s[j];
 	
 	forall (j in jobs) sum(m in machines, t in time) t * x[j][m][t] >= a[j];
 	
 	forall (j in jobs) p[j] + sum(m in machines, t in time) t * x[j][m][t] == c[j];
 	
 	forall (j in jobs) U[j] * T >= c[j] - d[j];	
 	
 	forall (j in jobs) Tardiness[j] >= 0;
 	
 	forall (j in jobs) Tardiness[j] >= c[j] - d[j];
 };

execute
{
  var j;
  var m;
  var t;
  for (j in jobs)
  {
  	for (m in machines)
  	{
  		for( t=0;t<=T;t++)
  		{
  			if (x[j][m][t] == 1)
  			{
  			  writeln("job:" + j + "; start:" + t + "; board: " + m + "; c[j]:" + c[j] + ";T[j]:" + Tardiness[j]);
   			}
    	}   			
    }   			
  }   			       			  
}  

//main
//{
//  var inputFilename = "..\\Problems\\RandomGeneration\\m8j5d15_1.csv";
//  var inFile = new IloOplInputFile(inputFilename);
//  
//  var jobs = new Array();
//  var readytimes = new Array();
//  var processtimes = new Array();
//  var duedates = new Array();
//  var sizes = new Array();
//  var boards_number;
//  var line;
//  line = inFile.readline();
//  boards_number = parseInt(line);
//
//  while (!inFile.eof)
//  {
//    line = inFile.readline();
//    writeln(line);
//    var data = line.split(",");
//    var j =parseInt(data[0]); 
//    jobs[j] = j; 
//    processtimes[j] = parseInt(data[1]);
//    duedates[j] = parseInt(data[2]);
//    sizes[j] = parseInt(data[3]);
//    readytimes[j] = parseInt(data[3]);
//  }    
//  inFile.close();
//  
//  var temp = new IloOplOutputFile("temp.dat");
//  
//  temp.writeln("jobs = {" + jobs.join(",") + "};");
//  temp.writeln("M = " + boards_number + ";");
//  temp.writeln("p = [" +  processtimes.join(",") + "];");
//  temp.writeln("d = [" +  processtimes.join(",") + "];");
//  temp.writeln("s = [" + sizes.join(",") + "];");
//  temp.writeln("a = [" + readytimes.join(",") + "];" );
//  
//  temp.close();
//  var data = new IloOplDataSource("temp.dat");
//  thisOplModel.addDataSource(data);
//  thisOplModel.generate();
//  
//  cplex.tilim = 300;
//  cplex.solve();    
//}