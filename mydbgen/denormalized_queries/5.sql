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
	and c_nationkey = s_nationkey
	and r_name = ':1'->replace with the two other regions (suppregion + custregion)
	and o_orderdate >= date ':2'
	and o_orderdate < date ':2' + interval '1' year
group by
	n_name ->replace with one
order by
	revenue desc;
:n -1
