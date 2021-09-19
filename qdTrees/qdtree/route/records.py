import jsonpickle
import pandas as pd

from qdTrees.config.appconfig import AppConfig
from qdTrees.queryparsing.treeutils import TreeUtils


def route_records(config, df, qd_tree):
    TreeUtils.route_df_record_vect(qd_tree, config, df, True)


def read_records(config, qd_tree):
    chunk_size = 10 ** 6
    columns = config.get_config("columns")

    with pd.read_csv(config.get_config("record_file_path"),
                     encoding="ISO-8859-1",
                     sep='|',
                     names=columns,
                     index_col=False,
                     parse_dates=config.get_config("date_columns"),
                     chunksize=chunk_size) as reader:
        for chunk in reader:
            route_records(config, chunk, qd_tree)


def read_tree(config):
    woodblock_results_path = config.get_config("tree_save_dir_path") + "/" + config.get_config("tree_save_file_name")
    f = open(woodblock_results_path)
    json_str = f.read()
    woodblock_results = jsonpickle.decode(json_str)
    qd_tree = woodblock_results.get_qd_tree()
    return qd_tree


if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    app_config = AppConfig('../../config/qdTreeConfig.json')
    app_config.update_config("record_file_path", "../../data/my_line_item_2.tbl")
    read_tree(app_config)
