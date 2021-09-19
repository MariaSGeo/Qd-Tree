from collections import deque

import jsonpickle
import numpy as np
from gym import spaces
from gym.spaces import Dict, Box, MultiBinary
from ray.rllib import MultiAgentEnv
from ray.rllib.env.env_context import EnvContext
from ray.rllib.utils.framework import try_import_tf, try_import_torch

from qdTrees.queryparsing.qdtree import IterationResult
from qdTrees.queryparsing.queryparsing import get_query_files_cuts
from qdTrees.queryparsing.treeutils import TreeUtils
from qdTrees.recordprocessing.sample_records import sample

tf1, tf, tfv = try_import_tf()
torch, nn = try_import_torch()


class WoodBlockEnvMultiAgent(MultiAgentEnv):

    def render(self, mode='human'):
        pass

    def __init__(self, config: EnvContext):

        # config
        self.config = config
        self.custom_config = config.get("custom_config")

        # gym env related
        self.all_cuts, self.queries = get_query_files_cuts(self.custom_config)

        # action_mask - the actions that have been done - 0 | actions that have not yet been chosen - 1
        # avail_actions - all of the actions
        # state - the encoded representation of the node in question
        self.observation_space = Dict({
            "action_mask": Box(0, 1, shape=(len(self.all_cuts),)),
            "avail_actions": Box(-1, 1, shape=(len(self.all_cuts),)),
            "state": MultiBinary(len(self.all_cuts)),
        })
        self.action_mask = np.ones(len(self.all_cuts))
        self.avail_actions = np.ones(len(self.all_cuts))
        self.state = np.ones(len(self.all_cuts))
        self.obs = {}

        # masks to store for failed used to have the represenation for nodes that failed mainly.
        self.masks = {}

        self.action_space = spaces.Discrete(len(self.all_cuts))
        self.available_actions = range(0, len(self.all_cuts))
        # actual number of cuts applied
        self.applied_cuts = 0
        self.rewards = {}

        # qdTree related
        self.qd_tree_actions_taken = {}
        self.qd_tree_b = self.custom_config.get_config("b")
        self.qd_tree_root = TreeUtils.build_root(self.all_cuts,
                                                 self.custom_config.get_config("categorical_columns", []),
                                                 self.custom_config.get_config("categorical_columns_values", {}),
                                                 self.custom_config.get_config("columns_in_queries", {}),
                                                 self.custom_config.get_config("column_ranges", {}),
                                                 1)
        self.root_done = False
        # the queue used to build the tree
        self.qd_tree_build_queue = deque()
        self.qd_tree_build_queue.append(self.qd_tree_root)
        # node counter for node ids
        self.qd_tree_node_counter = 1
        # cuts tried to current node - in case a cut is not allowed it is appended here
        self.cuts_tried_to_current_node = []
        # used to be able to bring back the state we were before, before trying to apply multiple cuts to a node
        self.action_mask_before_current_node = np.ndarray.copy(self.action_mask)
        self.failed_nodes = {}

        # sample related
        self.sample = sample(self.custom_config)
        self.sample_size = self.sample.shape[0]
        self.sample_percentage = self.custom_config.get_config("sample_fraction", 0.01)
        self.sample_path = self.custom_config.get_config("record_file_path")

        print('Environment initialized')

    def reset(self):
        print('Resetting Environment')
        self.qd_tree_root = TreeUtils.build_root(self.all_cuts,
                                                 self.custom_config.get_config("categorical_columns", []),
                                                 self.custom_config.get_config("categorical_columns_values", {}),
                                                 self.custom_config.get_config("columns_in_queries", {}),
                                                 self.custom_config.get_config("column_ranges", {}),
                                                 1)
        self.qd_tree_build_queue = deque()
        self.qd_tree_build_queue.append(self.qd_tree_root)
        self.root_done = False
        self.qd_tree_actions_taken = {}
        self.qd_tree_node_counter = 1
        self.applied_cuts = 0

        self.reset_observation_space()
        self.cuts_tried_to_current_node = []
        self.masks = {}
        self.action_mask_before_current_node = np.ndarray.copy(self.action_mask)
        self.masks[0] = np.ndarray.copy(self.action_mask)
        self.obs.update({"0": {
            "action_mask": self.action_mask,
            "avail_actions": self.avail_actions,
            "state": self.state
        }})
        # initial state observation - 0 -> root
        return {"0": {
            "action_mask": self.action_mask,
            "avail_actions": self.avail_actions,
            "state": self.state
        }}

    # reset observation values to start a new episode
    def reset_observation_space(self):
        self.action_mask = np.ones(len(self.all_cuts))
        self.avail_actions = np.ones(len(self.all_cuts))
        self.state = np.ones(len(self.all_cuts))

    # try to apply an action
    def step(self, actions):
        assert len(actions) == 1  # one at a time processing, one agent each time
        obs, rew, done, info = {}, {}, {}, {}
        action_mask_to_put = np.ndarray.copy(self.action_mask_before_current_node)
        allowed = False
        for agent, action in actions.items():
            finished = False
            action = int(action)

            # apply the cut and if it is legal update the env else revert the change
            allowed, c_node = self.allow_cut(action)
            if allowed:
                self.obs.update({str(c_node.get_block_id()): {
                    "action_mask": self.action_mask,
                    "avail_actions": self.avail_actions,
                    "state": c_node.get_encoded()
                }})
                self.update_environment(action)
                self.cuts_tried_to_current_node = []
                # update env values necessary for the model

                # keep current mask in case it is needed to revert back
                # needed in case we have tried different cuts
                self.action_mask = self.action_mask_before_current_node
                self.update_environment(action)
                self.action_mask_before_current_node = np.ndarray.copy(self.action_mask)
                self.applied_cuts = self.applied_cuts + 1

            else:
                self.qd_tree_node_counter = self.qd_tree_node_counter - 2
                if not self.root_done:
                    self.qd_tree_build_queue = deque()
                    self.qd_tree_build_queue.append(self.qd_tree_root)

                self.cuts_tried_to_current_node.append(action)

                self.obs.update({str(c_node.get_block_id()): {
                    "action_mask": self.action_mask,
                    "avail_actions": self.avail_actions,
                    "state": c_node.get_encoded()
                }})
                # remove cut from candidate cuts by masking it out
                self.update_action_mask(action)

            # check if finished for node - no more legal cuts
            if np.count_nonzero(self.action_mask) == 0:
                self.qd_tree_build_queue.popleft()

            # emit episode observation and rewards after routing the sample
            if len(self.qd_tree_build_queue) == 0 or self.applied_cuts == len(self.all_cuts):
                self.route_sample_records()
                self.rewards = self.calculate_rewards()
                self.print_tree_to_file()

                return self.obs, self.rewards, {"__all__": True}, {"0": {"root": self.qd_tree_root}}

        # pop the next node from the queue
        next_nodes = [self.qd_tree_build_queue[0]]
        if allowed:
            action_mask_to_put = self.action_mask

        self.masks.update({next_nodes[0].get_block_id(): np.ndarray.copy(action_mask_to_put)})
        obs.update({str(node.get_block_id()): self.build_current_node_state(node) for node in next_nodes})
        rew.update({str(node.get_block_id()): 0 for node in next_nodes})
        done.update({"__all__": False})
        info.update({str(node.get_block_id()): {} for node in next_nodes})

        return obs, rew, done, info

    # route the sample records using np and pd
    def route_sample_records(self):
        # self.sample.apply(self.route_sample_record, axis=1) apply proved too slow
        TreeUtils.route_df_record_vect(self.qd_tree_root, self.custom_config, self.sample, False)

    # calculate all rewards for each node and cut
    def calculate_rewards(self):
        # map of {block_id: rewards}
        result = {}
        self.get_normalized_rewards(self.qd_tree_root, result)
        self.update_failed_rewards(result)
        return result

    def update_failed_rewards(self, rewards):  # self.failed_nodes
        to_update = set(self.obs) - set(rewards)
        for node_id in to_update:
            rewards[node_id] = 0

        to_update = set(rewards) - set(self.obs)
        for node_id in to_update:
            del rewards[node_id]
        return rewards

    # make the cut and evaluate
    def allow_cut(self, action):
        # retrieve cut
        cut = self.all_cuts[action]

        # only used to check if a cut has been applied to the root
        if self.qd_tree_build_queue[0].get_block_id() == 0:
            is_root = True
        else:
            is_root = False

        # build node and update queue
        current_node, self.qd_tree_build_queue, self.qd_tree_node_counter = TreeUtils.add_cut_to_tree(cut,
                                                                                                      self.qd_tree_build_queue,
                                                                                                      self.qd_tree_node_counter,
                                                                                                      action)
        # route the sample records and check if the number of records for left and right satisfy the constrain
        self.route_sample_records()
        target_size = self.sample_percentage * self.qd_tree_b

        if current_node.get_left().get_records() >= target_size and current_node.get_right().get_records() >= target_size:
            if is_root:
                self.root_done = True
            return True, current_node
        else:

            # revert node construction and add to failed nodes
            current_node.set_is_leaf(True)
            self.qd_tree_build_queue.pop()
            self.qd_tree_build_queue.pop()
            self.qd_tree_build_queue.appendleft(current_node)
            self.failed_nodes[str(current_node.get_block_id())] = self.build_current_node_state(current_node)
            return False, current_node

    # update the action mask with the action used
    def update_environment(self, action):
        self.update_action_mask(action)

    def update_action_mask(self, action):
        self.action_mask[action] = 0

    def get_normalized_rewards(self, node, result):
        node_rewards = self.get_normalized_rewards_for_node(node)
        if not node_rewards == {}:
            result.update(node_rewards)
        if node is not None and not node.get_is_leaf():
            self.get_normalized_rewards(node.get_left(), result)
            self.get_normalized_rewards(node.get_right(), result)

    def get_normalized_rewards_for_node(self, node):
        number_of_skipped_records = 0
        for query, cuts in self.queries.items():
            if node.get_is_leaf():
                number_of_skipped_records += node.get_records()
            elif node.evaluate_query_against_metadata(self.custom_config, cuts):
                number_of_skipped_records += (2 * node.get_left().get_records())

        if node.get_records() == 0:
            return {str(node.get_block_id()): 0}
        normalized_records = number_of_skipped_records / (len(self.queries) * node.get_records())
        if node.get_is_leaf():
            return {}
        return {str(node.get_block_id()): normalized_records}

    def build_node_state(self, node):
        if node.get_block_id() not in self.masks:
            return {}
        return {
            "action_mask": self.masks[node.get_block_id()],
            "avail_actions": self.avail_actions,
            "state": node.get_encoded()
        }

    def build_current_node_state(self, node):
        return {
            "action_mask": self.action_mask,
            "avail_actions": self.avail_actions,
            "state": node.get_encoded()
        }

    def build_state(self, node, result):
        node_state = self.build_node_state(node)
        if node_state == {}:
            return
        result.update({str(node.get_block_id()): node_state})
        if node is not None and not node.get_is_leaf():
            self.build_state(node.get_left(), result)
            self.build_state(node.get_right(), result)

    def print_tree_to_file(self):
        self.json_serialize(self.custom_config.get_config("tree_save_dir_path") + "/" + self.custom_config.get_config(
            "tree_save_file_name"))

    def json_serialize(self, filename):
        f = open(filename, 'w')
        results = IterationResult(self.qd_tree_root, self.rewards)
        json_obj = jsonpickle.encode(results)
        f.write(json_obj)
        f.close()
