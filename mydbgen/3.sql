-- $ID$
-- TPC-H/TPC-R Shipping Priority Query (Q3)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	o_orderkey,
	sum(l_extendedprice * (1 - l_discount)) as revenue,
	o_orderdate,
	o_shippriority
from
	lineitem
where
	c_mktsegment = ':1'
	and o_orderdate < date ':2'
	and l_shipdate > date ':2'
group by
	l_orderkey,
	o_orderdate,
	o_shippriority
order by
	revenue desc,
	o_orderdate;
:n 10
