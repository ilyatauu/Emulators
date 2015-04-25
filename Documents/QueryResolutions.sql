-- Test for file field manipulations
select left([file],11),right([file],10),substring([file],4,3), * from results

select  left([file],9),right([file],10)
	,avg(rpfguan_penalty_time) GuanTime
	, avg(tbasedw_penalty_time) TBased2Time
	--,stdev(rpfguan_penalty_time)
	--,stdev(tbasedw_penalty_time)
from results
where ([file] not like '%j25%' and [file] not like '%j30%')
group by left([file],9), right([file],10)
ORDER BY left([file],9), right([file],10)

-- Average job calculation
select * from 
(
select  substring([file],5,2) number_of_jobs,
	avg(rpfguan_penalty_time) GuanTimeOptimal
	,avg(tbasedw_penalty_time) TBased2TimeOptimal
from results
where ([file] like '%f1%') and rpfguan_penalty_optimal=1
group by substring([file],5,2)
) o
join 
(
select  substring([file],5,2) number_of_jobs,
	avg(rpfguan_penalty_time) GuanTime
	,avg(tbasedw_penalty_time) TBased2Time
from results
where ([file] like '%f1%')
group by substring([file],5,2)
) a
on o.number_of_jobs = a.number_of_jobs
ORDER BY a.number_of_jobs

select  left([file],9),right([file],10),avg(rpfguan_penalty_time) GuanTime, avg(tbasedw_penalty_time) TBased2Tim
from results
where ([file] like '%j25%') and ([file] like '%f1%')
group by left([file],9), right([file],10)
ORDER BY left([file],9), right([file],10)


-- Check that all the solutions are equal
select r1.[file],r2.[file], 
	r1.tbasedw_penalty_solution - r2.tbasedw_penalty_solution,
	r1.tbasedw_penalty_solution - r2.rpfguan_penalty_solution
from results r1
join results r2
on left(r1.[file],11) = left(r2.[file],11)
where r1.tbasedw_penalty_solution - r2.rpfguan_penalty_solution <> 0
--where left(r1.[file],9) = 'm05j10d02'


-- Check difference resolutions
select  right([file],10)
	,avg(rpfguan_penalty_time) GuanTime
	,avg(tbasedw_penalty_time) TBased2Time
	,stdev(rpfguan_penalty_time) std_guan
	,stdev(tbasedw_penalty_time) std_tbasedw
	,max(rpfguan_penalty_time) max_rpfguan_penalty_time
	,min(rpfguan_penalty_time) min_rpfguan_penalty_time
	,sum(rpfguan_penalty_time) sum_GuanTime
	,sum(tbasedw_penalty_time) sum_TBased2Time
	,count(*) Number_of_problems
from results
where ([file] not like '%j25%' and [file] not like '%j30%')
group by right([file],10)
ORDER BY right([file],10)




