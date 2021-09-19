import random

import pandas as pd

from qdTrees.config.appconfig import AppConfig


def sample(config):
    # load the columns to use as headers
    columns = config.get_config("columns")
    p = config.get_config("sample_fraction", 0.01)  # 1% of the lines

    # if random from [0,1] interval is greater than 0.01 the row will be skipped
    # ref stack overflow
    sampled_records = pd.read_csv(config.get_config("record_file_path"),
                                  encoding="ISO-8859-1",
                                  sep='|',
                                  names=columns,
                                  index_col=False,
                                  skiprows=lambda i: i > 0 and random.random() > p,
                                  parse_dates=config.get_config("date_columns"))

    return sampled_records


if __name__ == "__main__":

    pd.set_option('display.max_columns', None)
    app_config = AppConfig('../config/qdTreeConfig.json')
    app_config.update_config("record_file_path", "../../data/my_line_item_2.tbl")
    app_config.update_config("sample_fraction", 0.001)
    records = sample(app_config)
    print(records.head(1))
    print(records.shape[0])
    print(records.l_quantity.unique())
    print(records.l_commitdate.unique())
    pd.to_datetime('1994-12-12')


