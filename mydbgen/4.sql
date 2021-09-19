-- $ID$
-- TPC-H/TPC-R Order Priority Checking Query (Q4)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	o_orderpriority,
	count(*) as order_count
from
	lineitem
where
	o_orderdate >= date ':1'
	and o_orderdate < date ':1' + interval '3' month
	and l_commitdate < l_receiptdate

group by
	o_orderpriority
order by
	o_orderpriority;
:n -1
