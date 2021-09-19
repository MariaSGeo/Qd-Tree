-- $ID$
-- TPC-H/TPC-R Product Type Profit Measure Query (Q9)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	nation,
	o_year,
	sum(amount) as sum_profit
from
	(
		select
            s_nation_name as nation,
			extract(year from o_orderdate) as o_year,
			l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity as amount
		from
			lineitem,
		where
			and p_name like '%:1%'
	) as profit
group by
	nation,
	o_year
order by
	nation,
	o_year desc;
:n -1
