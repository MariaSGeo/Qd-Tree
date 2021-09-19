-- $ID$
-- TPC-H/TPC-R Local Supplier Volume Query (Q5)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	n_name,
	sum(l_extendedprice * (1 - l_discount)) as revenue
from
	lineitem
where

	c_region_name = s_region_name
	and c_region_name = ':1'
	and o_orderdate >= date ':2'
	and o_orderdate < date ':2' + interval '1' year
group by
    c_nation_name
order by
	revenue desc;
:n -1
