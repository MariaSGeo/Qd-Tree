# Database Systems Project
## Qd-Trees 
###Maria-Sofia Georgaki


This is an implementation of the deep reinforcement learning algorithm proposed
in paper.

To generate the records required, in the mydbgen file run ```./dbgen -v -s 1 -T L``` 
With the scale factor set to 1 the records file takes up about 6GBs. set the -s parameter accordingly
There is the init.sql script to create the table lineitem

The templates that can be used with this implementation of Qd-trees are the following:
1, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 19. They have been adapted accordingly to fit the new schema.
Each query must be in a separate file and in some that there are unprocessed additions to numbers, 
they need to be replaced by hand.


Each of the following commands to work as is, need to be run in the folder that contains each script or executable
For the python scripts I found out a bit late it is a bad practice to be executed like that.
Replace PYTHONPATH=path with your path in order to scan the necessary packages.


To generate a query from a template run  ```./qgen template_num```

To start the agent run ``PYTHONPATH=/home/msgeorgaki/cv/repos/QdTree python3 woodblock.py``
Please note that when each episode ends the tree is stored in a json file and can be read later.

To produce the queries to create the partitions in the database, and the block_id in predicate that needs to be added to the queries, run ```PYTHONPATH=/home/msgeorgaki/cv/repos/QdTree python3 queries.py```.

To route the records from the file through the tree ```PYTHONPATH=/home/msgeorgaki/cv/repos/QdTree python3 records.py```

The project was run mainly through intellij. 
Modify accordingly the qdTreeConfig.json file to match the corresponding paths in your system

The whole process is the following:

1. Generate data and queries
2. Run the agent to produce a tree
3. Create a database - the name should be configured to be used in the qdTreeConfig.json
4. Run the queries.py script
5. Run the scripts for the partitions
6. Append by hand the where block_id in clauses produced
7. Run the records.py script
8. Run the queries against the datatbase


