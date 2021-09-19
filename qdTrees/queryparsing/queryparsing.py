import glob
from datetime import datetime, timedelta

import sqlparse

from qdTrees.config.appconfig import AppConfig
from qdTrees.queryparsing.qdtree import Cut


# get the cut type according to metadata providied
def get_cut_type(config, left, right):
    enhanced = config.get_config("enhanced", "True")
    # columns_in_queries = config.get_config_as_set("columns_in_queries", [])
    categorical_columns = config.get_config_as_set("categorical_columns", [])
    columns = config.get_config_as_set("columns", [])
    if enhanced == "True" and right in columns:  # TODO columns in queries?
        return "EXTENDED_CUT"
    elif left in categorical_columns:
        return "CATEGORICAL"
    else:
        return "RANGE"


# get date at the appropriate format
def fix_date(date, config):
    date_parts = date.split()
    if len(date_parts) == 1:
        return
    actual_date = datetime.strptime(date_parts[1].replace("\'", ""), '%Y-%m-%d')

    if len(date_parts) > 2:
        op = date_parts[2]
        how_many = int(date_parts[4].replace("\'", ""))
        what = date_parts[5]
        if op == '-' and what == 'day':
            actual_date = actual_date - timedelta(days=how_many)
        elif op == '+' and what == 'day':
            actual_date = actual_date + timedelta(days=how_many)
        elif op == '-' and what == 'year':
            actual_date = actual_date - timedelta(days=365 * how_many)
        elif op == '+' and what == 'year':
            actual_date = actual_date + timedelta(days=365 * how_many)
        elif op == '-' and what == 'month':
            actual_date = actual_date - timedelta(days=30 * how_many)
        elif op == '+' and what == 'month':
            actual_date = actual_date + timedelta(days=30 * how_many)

    return actual_date.strftime('%Y-%m-%d')


def fix_column(column):
    column_parts = column.split()
    return column_parts[len(column_parts) - 1]


def fix_str(right):
    right = right.replace('\'', '')
    return right


# get corresponding cut
def get_cut_from_comparison(config, comparison: sqlparse.sql.Comparison):
    left = comparison.left.value
    right = comparison.right.value
    op = comparison.tokens[2].value
    if op == 'in':
        right = right.replace('(', '')
        right = right.replace(')', '')
    if config.get_config_as_dict("column_types").get(left, "") == 'DATE':
        right = fix_date(right, config)
    # if "." in right:
    #     fix_column(right)
    # if "." in left:
    #     fix_column(left)
    cut_type = get_cut_type(config, comparison.left.value, comparison.right.value)
    if cut_type == "CATEGORICAL":
        right = fix_str(right)
    return Cut(left, op, right, cut_type)


def extract_cuts(config, statement: sqlparse.sql.Statement, res):
    for token in statement.tokens:
        get_token_cuts(config, token, res)
    return res


# get recursively all cuts - skip simple tokens
def get_token_cuts(config, t, res):
    if type(t) != sqlparse.sql.Token:
        if type(t) == sqlparse.sql.Comparison:
            res.append(get_cut_from_comparison(config, t))
            return
        else:
            for t1 in t.tokens:
                get_token_cuts(config, t1, res)


# process a file individually - contains a single query
def process_query_file(config, q_path):
    final_result = []
    with open(q_path, 'r') as query_file:
        split_file = sqlparse.split(query_file)
        print(query_file)
        for s in split_file:
            stmts = sqlparse.parse(s)
            for stmt in stmts:
                extract_cuts(config, stmt, final_result)
    return remove_duplicate_cuts(final_result)


# get all cuts for all queries in txt files
def get_query_files_cuts(config):
    all_cuts = []
    query_dict = {}
    for query_file in glob.glob(config.get_config("query_dir_path", "../../data/queries") + "/*.txt"):
        qs = process_query_file(config, query_file)
        all_cuts.extend(qs)
        query_dict.update({query_file: qs})
    return all_cuts, query_dict
    # return get_test_cuts(), get_test_dict()
    # return remove_duplicate_cuts(all_cuts)


# remove duplicate cuts if they exist
def remove_duplicate_cuts(all_cuts):
    return list(set(all_cuts))


def get_test_cuts():
    return [
        Cut('l_shipmode', '=', 'SHIP', "CATEGORICAL"),
        Cut('l_shipmode', '=', 'AIR', "CATEGORICAL"),
        Cut('l_shipmode', '!=', 'RAIL', "CATEGORICAL"),
        Cut('c_mktsegment', '=', '26', "CATEGORICAL"),
        Cut('o_shippriority', '!=', 1, "CATEGORICAL")
    ]


def get_test_dict():
    return {
        "q1": [Cut('l_shipmode', '=', 'SHIP', "CATEGORICAL"), Cut('l_shipmode', '=', 'AIR', "CATEGORICAL")],
        "q2": [Cut('l_shipmode', '!=', 'RAIL', "CATEGORICAL"), Cut('c_mktsegment', '=', '26', "CATEGORICAL")],
        "q3": [Cut('o_shippriority', '!=', '1', "CATEGORICAL")]
    }


if __name__ == "__main__":
    app_config = AppConfig('../config/qdTreeConfig.json')
    app_config.update_config("query_dir_path", "../../data/queries")
    cuts, q_dict = get_query_files_cuts(app_config)
    print(cuts)
    print(q_dict)
    print(len(cuts))
