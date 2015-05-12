select * from results_big where rpfguan_penalty_optimal = 1
select * from results_big where tbasedw_penalty_optimal = 1

select avg(tbasedw_penaltygap),avg(rpfguan_penaltygap)  
	,avg(tbasedw_penaltybuild_time)
	,avg(rpfguan_penaltybuild_time)
	,avg(tbasedw_penalty_time)
	,avg(rpfguan_penalty_time) from results_big 
--where ([file] like '%m20%' )
where  ([file] like '%m30%')
	and tbasedw_penalty_optimal = 1
	
	--and rpfguan_penalty_solution > tbasedw_penalty_solution


select  from results_big 
where [file] like '%m15%' 
	and rpfguan_penalty_solution = tbasedw_penalty_solution

select avg(tbasedw_penaltygap),avg(rpfguan_penaltygap)  
	,avg(tbasedw_penaltybuild_time)
	,avg(rpfguan_penaltybuild_time)
	,avg(tbasedw_penalty_time)
	,avg(rpfguan_penalty_time)
from results_big 
where [file] like '%m15%' 
	--and [file] like '%p20%'
	 --and [file] like '%p25%'
	--and rpfguan_penalty_solution = tbasedw_penalty_solution