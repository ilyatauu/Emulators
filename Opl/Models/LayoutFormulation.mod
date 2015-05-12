int M = ...;

// This layout formulation was derived 
// from the book: Facilities Design. Sunderes Herragu
// This model is presented in section 5.6 and called ABSMODEL3


//int N = 3;

{int} jobs = ...;
int p[jobs] = ...;
int s[jobs] = ...;
int a[jobs] = ...;
int d[jobs] = ...;
int T = max(j in jobs)p[j] * card(jobs);

dvar float+ x[jobs];
dvar float+ y[jobs];
dvar boolean z[jobs, jobs];
dvar boolean U[jobs];
dvar float+ c[jobs];

dvar float Tardiness[jobs];
dvar float objValue;

dvar float+ x_plus[jobs,jobs];
dvar float+ x_minus[jobs,jobs];
dvar boolean x_ind[jobs,jobs];

dvar float+ y_plus[jobs,jobs];
dvar float+ y_minus[jobs,jobs];
dvar boolean y_ind[jobs,jobs];


minimize objValue;
subject to
{
  
   objValue == sum(j in jobs) 1000 * U[j] + sum(j in jobs) Tardiness[j];
   //objValue == sum(j in jobs) Tardiness[j];
   //objValue == sum(j in jobs) U[j];
   
  forall (j in jobs) U[j] * T >= c[j] - d[j];
  
  forall (i in jobs) 0.5 * p[i] + x[i] == c[i];
  
//  forall (i in jobs, j in jobs : i != j) abs(x[i] - x[j]) + T * z[i,j] >= 0.5 * (p[j] + p[i]);
//  
//  forall (i in jobs, j in jobs : i != j) abs(y[i] - y[j]) + M * (1-z[i,j]) >= 0.5 * (s[j] + s[i]);
  
  forall (i in jobs, j in jobs) x_plus[i,j] - x_minus[i,j] == x[i] - x[j];
  forall (i in jobs, j in jobs : i != j && i >j) x_minus[i,j] <= x_ind[i,j]*T;
  forall (i in jobs, j in jobs : i != j && i >j) x_plus[i,j] <= (1-x_ind[i,j])*T;  
  forall (i in jobs, j in jobs : i != j && i >j) x_plus[i,j] + x_minus[i,j] + T * z[i,j] >= 0.5 * (p[j] + p[i]);
  
  forall (i in jobs, j in jobs : i != j && i >j) y_plus[i,j] - y_minus[i,j] == y[i] - y[j];
  forall (i in jobs, j in jobs : i != j && i >j) y_minus[i,j] <= y_ind[i,j]*M;
  forall (i in jobs, j in jobs : i != j && i >j) y_plus[i,j] <= (1-y_ind[i,j])*M;  
  forall (i in jobs, j in jobs : i != j && i >j) y_plus[i,j] + y_minus[i,j] + M * (1-z[i,j]) >= 0.5 * (s[j] + s[i]);
  
  // point of half of each job size + half of job size must be smaller than number
  // or equal to last board, the last board is M
  forall (i in jobs) y[i] + 0.5 * s[i] <= M;
  
  forall (i in jobs) x[i] >= a[i] + 0.5 * p[i];
  
  forall (i in jobs) y[i] >= 0.5 * s[i];
  
  forall (j in jobs) Tardiness[j] >= 0;
 	
  forall (j in jobs) Tardiness[j] >= c[j] - d[j];
}  