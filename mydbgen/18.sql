-- $ID$
-- TPC-H/TPC-R Large Volume Customer Query (Q18)
-- Function Query Definition
-- Approved February 1998
:x
:o
select
	c_name,
	c_custkey,
	o_orderkey,
	o_orderdate,
	o_totalprice,
	sum(l_quantity)
from
	lineitem
where
	o_orderkey in (
		select
			o_orderkey
		from
			lineitem
		group by
			o_orderkey having
				sum(l_quantity) > :1
	)
group by
	c_name,
	c_custkey,
	o_orderkey,
	o_orderdate,
	o_totalprice
order by
	o_totalprice desc,
	o_orderdate;
:n 100
