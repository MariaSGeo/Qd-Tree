import copy
from collections import deque

import numpy as np
import pandas as pd

from qdTrees.dbConnection.connection import DatabaseSetupSqlAlchemy
from qdTrees.queryparsing.qdtree import Range, QdTreeNode, Cut


# class used for building the tree
class TreeUtils:

    # build the node.left and node.right categorical cats according to the cut being made
    @staticmethod
    def calculate_categorical_cut(node, cut):
        current_categorical_mask = node.get_categorical_mask()
        if cut.get_attr1() not in current_categorical_mask:
            current_categorical_mask[cut.get_attr1()] = {}
        if cut.get_attr2() not in current_categorical_mask[cut.get_attr1()]:
            current_categorical_mask[cut.get_attr1()][cut.get_attr2()] = 1
        left_categorical_mask = copy.deepcopy(current_categorical_mask)
        left_categorical_mask[cut.get_attr1()][cut.get_attr2()] = 1
        right_categorical_mask = copy.deepcopy(current_categorical_mask)
        right_categorical_mask[cut.get_attr1()][cut.get_attr2()] = 0
        return left_categorical_mask, right_categorical_mask

    # build the node.left and node.right extended cuts according to the cut being made
    @staticmethod
    def calculate_extended_cut(node, cut):
        current_categorical_mask_extended = node.get_categorical_mask_extended()
        left_categorical_mask_extended = copy.deepcopy(current_categorical_mask_extended)
        left_categorical_mask_extended[cut] = 1
        right_categorical_mask_extended = copy.deepcopy(current_categorical_mask_extended)
        right_categorical_mask_extended[cut] = 0
        return left_categorical_mask_extended, right_categorical_mask_extended

    # build the node.left and node.right range cuts according to the cut being made
    # the cuts is not checked logically, e.g for a node we may have ["inf", 10] if 20 comes to cut the space
    # then ["inf", 20] [20, 10] is produced. In this case it will be cut as a none allowed cut by the algorithm
    @staticmethod
    def calculate_range_cut(node, cut):
        if cut.get_attr1() not in node.get_ranges():
            node.get_ranges()[cut.get_attr1()] = Range('inf', 'inf')
        current_range = node.get_ranges()[cut.get_attr1()]
        left_range = copy.deepcopy(node.get_ranges())
        left_range[cut.get_attr1()] = Range(current_range.get_range_left(), cut.get_attr2())
        right_range = copy.deepcopy(node.get_ranges())
        right_range[cut.get_attr1()] = Range(cut.get_attr2(), current_range.get_range_right())
        return left_range, right_range

    # apply a cut according to its type and build the node.left and node.right leaves
    @staticmethod
    def apply_cut(node, cut, est, action):
        attr1, op, attr2, node_type = cut.get_cut_attributes()
        left_categorical_mask = node.get_categorical_mask()
        right_categorical_mask = node.get_categorical_mask()
        left_range_cut = node.get_ranges()
        right_range_cut = node.get_ranges()
        left_categorical_mask_extended = node.get_categorical_mask_extended()
        right_categorical_mask_extended = node.get_categorical_mask_extended()

        if node_type == "CATEGORICAL":
            left_categorical_mask, right_categorical_mask = TreeUtils.calculate_categorical_cut(node, cut)

        elif node_type == "RANGE":
            left_range_cut, right_range_cut = TreeUtils.calculate_range_cut(node, cut)

        elif node_type == "EXTENDED_CUT":
            left_categorical_mask_extended, right_categorical_mask_extended = TreeUtils.calculate_extended_cut(node,
                                                                                                               cut)

        left = QdTreeNode(None, left_range_cut, left_categorical_mask, est * node.get_records(),
                          left_categorical_mask_extended)
        left_encoded = copy.deepcopy(node.get_encoded())
        left.set_encoded(left_encoded)
        right = QdTreeNode(None, right_range_cut, right_categorical_mask, (1 - est) * node.get_records(),
                           right_categorical_mask_extended)
        right_encoded = copy.deepcopy(node.get_encoded())
        right_encoded[action] = 0
        right.set_encoded(right_encoded)
        return left, right

    # add the cut to the current node and update accordingly
    @staticmethod
    def add_cut_to_tree(cut, queue, node_counter, action):
        current_node = queue.popleft()
        # print('Adding cut to ', current_node.get_block_id())
        current_node.set_node_cut(cut)
        left, right = TreeUtils.apply_cut(current_node, cut, 0.1, action)
        current_node.set_is_leaf(False)
        left.set_is_leaf(True)
        left.set_block_id(node_counter)
        right.set_is_leaf(True)
        right.set_block_id(node_counter + 1)
        current_node.set_left(left)
        current_node.set_right(right)
        queue.append(left)
        queue.append(right)
        return current_node, queue, node_counter + 2

    # build the root node by providing some metadata for the tree construction
    @staticmethod
    def build_root(cuts, categorical, categorical_values, columns_in_queries, ranges, n_records):

        root_cut = Cut("I", "am", "root", "ROOT")
        node_ranges = {}
        categorical_mask = {}
        categorical_mask_columns = {}
        records = n_records

        for cut in cuts:
            if cut.get_attr2() in columns_in_queries:
                categorical_mask_columns[cut] = 1
            elif cut.get_attr1() in categorical_values:  # before was in categorical
                for key, values in categorical_values.items():
                    categorical_mask[key] = {}
                    for value in values:
                        categorical_mask[key][value] = 1
            else:
                if cut.get_attr1() in ranges:
                    node_ranges[cut.get_attr1()] = Range(ranges[cut.get_attr1()][0], ranges[cut.get_attr1()][1])

        node = QdTreeNode(root_cut, node_ranges, categorical_mask, records, categorical_mask_columns)
        node.set_encoded(np.ones(len(cuts)))
        node.set_block_id(0)
        return node

    @staticmethod
    def build_tree(cuts, categorical, categorical_values, columns_in_queries, ranges, n_records):
        root = TreeUtils.build_root(cuts, categorical, categorical_values, columns_in_queries, ranges, n_records)
        queue = deque()
        queue.append(root)
        node_counter = 0
        for cut in cuts:
            current_node, queue, node_counter = TreeUtils.add_cut_to_tree(cut, queue, node_counter, 1)
        return root

    # route the dataframe using pandas and numpy functions for vectorized methods and faster execution
    @staticmethod
    def route_df_record_vect(current_node, config, df, write_to_db):
        current_node.set_records(df.shape[0])

        if current_node.get_is_leaf():
            if write_to_db:
                TreeUtils.write_df_to_db(TreeUtils.update_df_with_block_id(df, current_node), config)
            return
        node_type = current_node.get_node_cut().get_node_type()
        if node_type == "CATEGORICAL":
            left, right = TreeUtils.evaluate_record_categorical(current_node, df)
        elif node_type == "RANGE":
            left, right = TreeUtils.evaluate_record_range(current_node, df, config)
        elif node_type == "EXTENDED_CUT":
            left, right = TreeUtils.evaluate_record_extended(current_node, df)

        TreeUtils.route_df_record_vect(current_node.get_left(), config, left, write_to_db)
        TreeUtils.route_df_record_vect(current_node.get_right(), config, right, write_to_db)

    # update with the block id
    @staticmethod
    def update_df_with_block_id(df, current_node):
        df["block_id"] = current_node.get_block_id()
        return df

    # write the records to the database
    @staticmethod
    def write_df_to_db(df, config):
        db = DatabaseSetupSqlAlchemy(config)
        db.insert_df_to_db(df)
        return

    # split records to left and right by using the cut of the node - Categorical cut assume equality or inequality
    # in is not currently supported
    @staticmethod
    def evaluate_record_categorical(root, df):
        col_name = root.get_node_cut().get_attr1()
        cond = np.equal(df[col_name], root.get_node_cut().get_attr2())
        left = df[cond]
        right = df[~cond]
        if root.get_node_cut().get_op() == "!=" or root.get_node_cut().get_op() == "<>":
            return right, left
        return left, right

    # # split records to left and right by using the cut of the node - Categorical cut
    # @staticmethod
    # def evaluate_record_categorical(root, df):
    #     col_name = root.get_node_cut().get_attr1()
    #     op = root.get_node_cut().get_op()
    #     if op == "IN" or op == "in":  # TODO in handling
    #         all_ins = root.get_node_cut().split()
    #         return df, pd.DataFrame(columns=df.columns)
    #     else:
    #         cond = np.equal(df[col_name], root.get_node_cut().get_attr2())
    #         left = df[cond]
    #         right = df[~cond]
    #         if root.get_node_cut().get_op() == "!=" or root.get_node_cut().get_op() == "<>":
    #             return right, left
    #         return left, right

    # split records to left and right by using the cut of the node - Range cut
    @staticmethod
    def evaluate_record_range(root, df, config):
        col_name = root.get_node_cut().get_attr1()
        val = root.get_node_cut().get_attr2()
        op = root.get_node_cut().get_op()
        values_map = config.get_config_as_dict("column_types")
        # print(col_name, " ", df.shape[0])
        if col_name not in values_map:
            return df, pd.DataFrame(columns=df.columns)
        # print("record_range_df_comparison", col_name, " ", op, " ", val)
        values_config = values_map[col_name]
        if values_config == "DOUBLE":
            val = float(val)
        elif values_config == 'INT':
            val = int(val)
        elif values_config == 'DATE':
            val = np.datetime64(val)
        # if col_name == "l_quantity":
        #     print('holla')
        if op == ">=":
            cond = np.greater_equal(df[col_name], val)
            return df[cond], df[~cond]
        elif op == ">":
            cond = np.greater(df[col_name], val)
            return df[cond], df[~cond]
        elif op == "<=":
            cond = np.less_equal(df[col_name], val)
            return df[cond], df[~cond]
        elif op == "<":
            cond = np.less(df[col_name], val)
            return df[cond], df[~cond]
        pass

    # split records to left and right by using the cut of the node - Extended cut
    @staticmethod
    def evaluate_record_extended(root, df):
        col_name1 = root.get_node_cut().get_attr1()
        col_name2 = root.get_node_cut().get_attr2()
        cond = np.equal(df[col_name1], df[col_name2])
        left = df[cond]
        right = df[~cond]
        return left, right

    # print a tree by level
    @staticmethod
    def print_tree_by_level(root):
        if root is None:
            return
        q = [root]
        while q:
            count = len(q)
            while count > 0:
                temp = q.pop(0)
                if not temp.get_is_leaf():
                    print(temp.get_node_cut().get_cut_attributes())
                else:
                    print("LEAF")
                    count -= 1
                    continue
                if temp.left:
                    q.append(temp.left)
                if temp.right:
                    q.append(temp.right)

                count -= 1
            print(' ')

    # gets tree leaves
    @staticmethod
    def get_tree_leaves(root):
        all_leaves = []
        count2 = 0
        if root is None:
            return
        q = [root]
        # print("--------------IDS------------------")
        while q:
            count = len(q)
            count2 = count2+ count

            while count > 0:
                temp = q.pop(0)
                print(temp.get_block_id())
                if temp.get_is_leaf():
                    all_leaves.append(temp)
                    count -= 1
                    continue
                if temp.left:
                    q.append(temp.left)
                if temp.right:
                    q.append(temp.right)

                count -= 1
        # print("--------------IDS------------------")
        print(count2)
        return all_leaves
