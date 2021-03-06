
select avg(tbasedw_penalty_time) avg_tbased, 
	STDEV(tbasedw_penalty_time) std_tbased, 
	avg(rpfguan_penalty_time) avg_guan, 
	STDEV(rpfguan_penalty_time) std_guan,
	count(*)
from (
SELECT * FROM [Emulators].[dbo].[results_120_set3]
union all 
SELECT * FROM [Emulators].[dbo].[results_120_set4]
) x
where [file] like '%p20%'
	and tbasedw_penalty_optimal = 1
	and rpfguan_penalty_optimal = 1


select rpfguan_penalty_time,  
	PERCENTILE_DISC(0.5) within group (order by rpfguan_penalty_time) over() median_guan,
	PERCENTILE_DISC(0.5) within group (order by tbasedw_penalty_time) over() median_tbased
from (
SELECT * FROM [Emulators].[dbo].[results_120_set3]
union all 
SELECT * FROM [Emulators].[dbo].[results_120_set4]
) x
where [file] like '%p20%'
	and rpfguan_penalty_optimal = 1
	and tbasedw_penalty_optimal = 1