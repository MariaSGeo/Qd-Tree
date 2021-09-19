-- $ID$
-- TPC-H/TPC-R Small-Quantity-Order Revenue Query (Q17)
-- Functional Query Definition
-- Approved February 1998
:x
:o
select
	sum(l_extendedprice) / 7.0 as avg_yearly
from
	lineitem
where
	p_brand = ':1'
	and p_container = ':2'
	and l_quantity < 0.2 * avg(l_quantity)

:n -1
