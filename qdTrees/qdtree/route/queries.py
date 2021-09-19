import jsonpickle
import pandas as pd

from qdTrees.config.appconfig import AppConfig
from qdTrees.queryparsing.queryparsing import get_query_files_cuts
from qdTrees.queryparsing.treeutils import TreeUtils


def route_queries(config, qd_tree, qd_tree_leaves):
    all_cuts, queries = get_query_files_cuts(config)

    updated_queries = []
    for query, cuts in queries.items():
        query = query + " block_id in ("
        for leaf in leaves:
            if leaf.evaluate_query_against_metadata(config, cuts):
                query = query + " " + str(leaf.get_block_id()) + ","

        query = query[:-1]
        query = query + ")"
        updated_queries.append(query)
        print(query)


def read_tree(config):
    woodblock_results_path = config.get_config("tree_save_dir_path") + "/" + config.get_config("tree_save_file_name")
    f = open(woodblock_results_path)
    json_str = f.read()
    woodblock_results = jsonpickle.decode(json_str)
    qd_tree = woodblock_results.get_qd_tree()
    return qd_tree


def print_partition_queries(config, leaves):
    filename = config.get_config("partition_query_dir_path") + "/" + config.get_config("partition_query_file_name")
    table_name = config.get_config("db")["table"]
    f = open(filename, 'w')
    for leaf in leaves:
        q_string = "create table " + table_name + "_" + str(leaf.get_block_id()) + \
                   " partition of " + table_name + " for values in (" + str(leaf.get_block_id()) + ");\n"
        f.write(q_string)
    f.close()


def get_leaves(qd_tree):
    return set(TreeUtils.get_tree_leaves(qd_tree))


#     create table lineitem_1
# partition of lineitem
# for values in (1);

if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    app_config = AppConfig('../../config/qdTreeConfig.json')
    app_config.update_config("record_file_path", "../../data/my_line_item_2.tbl")
    qd_Tree = read_tree(app_config)
    leaves = get_leaves(qd_Tree)
    print_partition_queries(app_config, leaves)
    route_queries(app_config, qd_Tree, leaves)
