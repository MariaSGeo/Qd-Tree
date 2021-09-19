from sqlalchemy import create_engine

from qdTrees.config.appconfig import AppConfig
from qdTrees.recordprocessing.sample_records import sample


# used to connect to the db and save the dataframes
class DatabaseSetupSqlAlchemy:

    def __init__(self, config):
        db_config = config.get_config("db")
        self.table = db_config["table"]
        self.uri = db_config["connection_uri"]
        self.engine = create_engine(self.uri, echo="debug")

    # insert dataframes to a specific table
    def insert_df_to_db(self, data):
        data.to_sql(self.table,
                    self.engine,
                    if_exists="append",
                    index=False)


if __name__ == '__main__':
    config = AppConfig("../config/qdTreeConfig.json")
    db_setup = DatabaseSetupSqlAlchemy(config)
    config.update_config("record_file_path", "../../data/my_line_item_2.tbl")
    config.update_config("sample_fraction", 0.0001)

    df = sample(config)
    df['block_id'] = 1
    print(df.shape[0])
    db_setup.insert_df_to_db(df)

#     create table lineitem_1
# partition of lineitem
# for values in (1);
