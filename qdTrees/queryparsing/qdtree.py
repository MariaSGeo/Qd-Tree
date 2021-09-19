import numpy as np


class IterationResult(object):

    def __init__(self, qd_tree, rewards):
        self.qd_tree = qd_tree
        self.rewards = rewards

    def get_qd_tree(self):
        return self.qd_tree

    def set_qd_tree(self, qd_tree):
        self.qd_tree = qd_tree

    def get_rewards(self):
        return self.rewards

    def set_rewards(self, rewards):
        self.rewards = rewards


# Object used to describe ranges
class Range(object):
    def __init__(self, range_left, range_right):
        self.range_left = range_left
        self.range_right = range_right

    def get_range_left(self):
        return self.range_left

    def set_range_left(self, range_left):
        self.range_left = range_left

    def get_range_right(self):
        return self.range_right

    def set_range_right(self, range_right):
        self.range_right = range_right

    def print(self):
        print(self.range_left, " ", self.range_right)


# Object used to describe cuts
class Cut(object):
    def __init__(self, attr1, op, attr2, node_type):
        self.attr1 = attr1
        self.op = op
        self.attr2 = attr2
        self.node_type = node_type

    def key(self):
        return (self.attr1, self.op, self.attr2, self.node_type)

    def __hash__(self):
        return hash(self.key())

    def __eq__(self, other):
        if isinstance(other, Cut):
            return self.key() == other.key()
        return NotImplemented

    def get_attr1(self):
        return self.attr1

    def set_attr1(self, attr1):
        self.attr1 = attr1

    def get_op(self):
        return self.op

    def set_op(self, op):
        self.op = op

    def get_attr2(self):
        return self.attr2

    def set_attr2(self, attr2):
        self.attr2 = attr2

    def get_cut_attributes(self):
        return self.attr1, self.op, self.attr2, self.node_type

    def set_node_type(self, node_type):
        self.node_type = node_type

    def get_node_type(self):
        return self.node_type

    def print(self):
        print(self.attr1, " ", self.op, " ", self.attr2, " ", self.node_type)


class QdTreeNode(object):
    def __init__(self, node_cut, node_ranges, categorical_mask, records, categorical_mask_extended):
        self.node_cut = node_cut
        self.node_ranges = node_ranges
        self.categorical_mask = categorical_mask
        self.records = records
        self.categorical_mask_extended = categorical_mask_extended
        self.left = None
        self.right = None
        self.is_leaf = False
        self.block_id = None
        self.encoded = None

    def set_encoded(self, encoded):
        self.encoded = encoded

    def get_encoded(self):
        return self.encoded

    def get_node_type(self):
        if self.node_ranges is not None and \
                (self.categorical_mask is not None or self.categorical_mask_extended is not None):
            return "BOTH"
        if self.node_ranges is not None:
            return "RANGE"
        if self.categorical_mask is not None or self.categorical_mask_extended is not None:
            return "CATEGORICAL"

    def get_ranges(self):
        return self.node_ranges

    def set_range(self, node_ranges):
        self.node_ranges = node_ranges

    def get_categorical_mask(self):
        return self.categorical_mask

    def set_categorical_mask(self, categorical_mask):
        self.categorical_mask = categorical_mask

    def get_node_cut(self):
        return self.node_cut

    def set_node_cut(self, node_cut):
        self.node_cut = node_cut

    def get_right(self):
        return self.right

    def set_right(self, right):
        self.right = right

    def get_left(self):
        return self.left

    def set_left(self, left):
        self.left = left

    def set_is_leaf(self, is_leaf):
        self.is_leaf = is_leaf

    def get_is_leaf(self):
        return self.is_leaf

    def set_block_id(self, block_id):
        self.block_id = block_id

    def get_block_id(self):
        return self.block_id

    def set_categorical_mask_extended(self, categorical_mask_extended):
        self.categorical_mask_extended = categorical_mask_extended

    def get_categorical_mask_extended(self):
        return self.categorical_mask_extended

    def set_records(self, records):
        self.records = records

    def get_records(self):
        return self.records

    def print_categorical_mask(self):
        for key, value in self.categorical_mask.items():
            key.print()
            print(value)

    def print_categorical_mask_extended(self):
        for key, value in self.categorical_mask_extended.items():
            key.print()
            print(value)

    def print_ranges(self):
        for key, value in self.node_ranges.items():
            print(key)
            print(value)

    def print(self):
        print("Cut")
        self.get_node_cut().print()
        print("Categorical Mask Extended")
        self.print_categorical_mask_extended()
        print("Categorical Mask")
        self.print_categorical_mask()
        print("Categorical Ranges")
        self.print_ranges()

    def evaluate_query_against_metadata(self, config, query_cuts):
        for cut in query_cuts:
            node_type = cut.get_node_type()
            if node_type == "CATEGORICAL":
                if self.evaluate_categorical_against_node_metadata(config, cut):
                    return True
            elif node_type == "RANGE":
                if self.evaluate_range_against_node_metadata(config, cut):
                    return True
            elif node_type == "EXTENDED_CUT":
                if self.evaluate_extended_against_node_metadata(config, cut):
                    return True
        return False

    def evaluate_query_against_all_metadata(self, config, query_cuts):
        pass


    def evaluate_categorical_against_node_metadata(self, config, cut):
        return cut.get_attr1() not in self.categorical_mask \
               or cut.get_attr2() not in self.categorical_mask[cut.get_attr1()] \
               or self.categorical_mask[cut.get_attr1()][cut.get_attr2()] == 1
        # return self.categorical_mask[cut.get_attr1()][cut.get_attr2()] == 1

    def evaluate_range_against_node_metadata(self, config, cut):
        # TODO evaluate against types
        values_map = config.get_config_as_dict("column_types")
        if cut.get_attr1() not in values_map:
            return True
        column_type = values_map[cut.get_attr1()]
        node_range = self.node_ranges.get(cut.get_attr1(), Range("inf", "inf"))
        node_range_left = node_range.get_range_left()
        node_range_right = node_range.get_range_right()
        query_value = cut.get_attr2()
        op = cut.get_op()
        if column_type == "INT":
            query_value = int(query_value)
            if node_range_left == "inf" and node_range_right == "inf":
                return True
            elif node_range_left == "inf":
                node_range_right = int(node_range_right)
            elif node_range_right == "inf":
                node_range_left = int(node_range_left)
            else:
                node_range_right = int(node_range_right)
                node_range_left = int(node_range_left)
        elif column_type == "DOUBLE":
            query_value = float(query_value)
            if node_range_left == "inf" and node_range_right == "inf":
                return True
            elif node_range_left == "inf":
                node_range_right = float(node_range_right)
            elif node_range_right == "inf":
                node_range_left = float(node_range_left)
            else:
                node_range_right = float(node_range_right)
                node_range_left = float(node_range_left)
        # TODO not supported ? - ordered and dictionary encoded to 1, 2, 3, etc
        elif column_type == "STR":
            return True
        elif column_type == "DATE":
            query_value = np.datetime64(query_value)
            if node_range_left == "inf" and node_range_right == "inf":
                return True
            elif node_range_left == "inf":
                node_range_right = np.datetime64(node_range_right)

            elif node_range_right == "inf":
                node_range_left = np.datetime64(node_range_left)

            else:
                node_range_left = np.datetime64(node_range_left)
                node_range_right = np.datetime64(node_range_right)

        self.cpm(node_range_left, op, node_range_right, query_value)

    def cpm(self, node_range_left, op, node_range_right, value):
        if node_range_left == "inf" and node_range_right == "inf":
            return True
        if op == ">=":
            if node_range_right == "inf":
                return True
            else:
                return value <= node_range_right
        elif op == ">":
            if node_range_right == "inf":
                return True
            else:
                return value < node_range_right
        elif op == "<=":
            if node_range_left == "inf":
                return True
            else:
                return node_range_left <= value
        elif op == "<":
            if node_range_left == "inf":
                return True
            else:
                return node_range_left < value

    def evaluate_extended_against_node_metadata(self, config, cut):
        return self.categorical_mask_extended.get(cut, 1) == 1
