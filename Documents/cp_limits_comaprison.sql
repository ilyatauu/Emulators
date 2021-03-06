/****** Script for SelectTopNRows command from SSMS  ******/

select l10s.pname, l10s.cp_penalty_solution, l10s.cp_penalty_time, 
	l1s.cp_penalty_solution, l1s.cp_penalty_time,
	l10s.cp_penalty_solution - l1s.cp_penalty_solution
from 
(
SELECT [file]
      ,[cp_penalty_solution]
      ,[cp_penalty_optimal]
      ,[cp_penalty_time]
	  ,left([file],11) pname
  FROM [Playground].[dbo].[results_cp_limits]
  where [file] not like '%limit%'
) l10s join
(
SELECT TOP 1000 [file]
      ,[cp_penalty_solution]
      ,[cp_penalty_optimal]
      ,[cp_penalty_time]
	  ,left([file],11) pname
  FROM [Playground].[dbo].[results_cp_limits]
  where [file] like '%limit3s%'  
) l1s
on l10s.pname = l1s.pname

SELECT TOP 1000 [file]
      ,[cp_penalty_solution]
      ,[cp_penalty_optimal]
      ,[cp_penalty_time]
	  ,left([file],11)
  FROM [Playground].[dbo].[results_cp_limits]
  where [file] like '%limit2s%'  

SELECT TOP 1000 [file]
      ,[cp_penalty_solution]
      ,[cp_penalty_optimal]
      ,[cp_penalty_time]
	  ,left([file],11)
  FROM [Playground].[dbo].[results_cp_limits]
  where [file] like '%limit3s%'  

