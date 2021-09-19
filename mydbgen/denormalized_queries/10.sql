-- $ID$
-- TPC-H/TPC-R Returned Item Reporting Query (Q10)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	c_custkey,
	c_name,
	sum(l_extendedprice * (1 - l_discount)) as revenue,
	c_acctbal,
	c_nationname,
	c_address,
	c_phone,
	c_comment
from
	lineitem
where
	l_orderkey = o_orderkey
	and o_orderdate >= date ':1'
	and o_orderdate < date ':1' + interval '3' month
	and l_returnflag = 'R'
group by
	c_custkey,
	c_name,
	c_acctbal,
	c_phone,
	c_nationname,
	c_address,
	c_comment
order by
	revenue desc;
:n 20
