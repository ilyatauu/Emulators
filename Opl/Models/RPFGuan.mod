// This relative position formulation 
// was derived from formulation presented in 
// a paper: The berth allocation problem models and solution methods. Y. Guan, 2004.


int M = ...;

//int N = 3;

{int} jobs = ...;
int p[jobs] = ...; // process time of a job
int s[jobs] = ...; // size of a job
int a[jobs] = ...; // arrival time of a job
int d[jobs] = ...; // due date of a job
int T = max(j in jobs)p[j] * card(jobs); // due date of all jobs


dvar float+ u[jobs];
dvar float+ v[jobs];
dvar float+ c[jobs];
dvar boolean ll[jobs,jobs];
dvar boolean bb[jobs,jobs];
dvar boolean U[jobs];
dvar float Tardiness[jobs];
dvar float objValue;


minimize objValue;
subject to
{
  
     objValue == sum(j in jobs) 1000 * U[j] + sum(j in jobs) Tardiness[j];
   //objValue == sum(j in jobs) Tardiness[j];
   //objValue == sum(j in jobs) U[j];
  

  forall (j in jobs) U[j] * T >= c[j] - d[j];
  
  forall (i in jobs, j in jobs: i != j) u[j]-u[i]-p[i]-(ll[i,j]-1)*T >= 0;
  
  forall (i in jobs, j in jobs: i != j) v[j]-v[i]-s[i]-(bb[i,j]-1)*M >= 0;
  
  forall (i in jobs, j in jobs: i != j && i >j) ll[i,j]+ll[j,i]+bb[i,j]+bb[j,i] >= 1;
  
  forall (i in jobs, j in jobs: i != j && i>j) ll[i,j]+ll[j,i] <= 1;
  
  forall (i in jobs, j in jobs: i != j && i>j) bb[i,j]+bb[j,i] <= 1;
  
  forall (i in jobs) p[i] + u[i] == c[i];
  
  forall (i in jobs) a[i] <=u[i];
  
  forall (i in jobs) v[i] <= M-s[i];
  
  forall (j in jobs) Tardiness[j] >= 0;
 	
  forall (j in jobs) Tardiness[j] >= c[j] - d[j];
};

