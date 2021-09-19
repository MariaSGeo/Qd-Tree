import argparse
import json
import os

import ray
from ray import tune
from ray.rllib.agents import ppo
from ray.rllib.models import ModelCatalog
from ray.rllib.utils.framework import try_import_tf, try_import_torch
from ray.rllib.utils.test_utils import check_learning_achieved
from ray.tune import grid_search
from ray.tune.logger import pretty_print

from qdTrees.config.appconfig import AppConfig
from qdTrees.queryparsing.treeutils import TreeUtils
from qdTrees.woodblock.custom_gym.envs.custom_env_dir import WoodblockCallbacks
from qdTrees.woodblock.custom_gym.envs.custom_env_dir.WoodblockCallbacks import WoodblockCallbacksClass
from qdTrees.woodblock.custom_gym.envs.custom_env_dir.woodblock_env import WoodBlockEnvMultiAgent
from qdTrees.woodblock.custom_gym.envs.custom_env_dir.woodblock_model import WoodBlockActionMaskModel

tf1, tf, tfv = try_import_tf()
torch, nn = try_import_torch()

parser = argparse.ArgumentParser()
parser.add_argument(
    "--run",
    type=str,
    default="PPO",
    help="The RLlib-registered algorithm to use.")
parser.add_argument(
    "--framework",
    choices=["tf", "tf2", "tfe", "torch"],
    default="tf",
    help="The DL framework specifier.")
parser.add_argument(
    "--as-test",
    action="store_true",
    help="Whether this script should be run as a test: --stop-reward must "
         "be achieved within --stop-timesteps AND --stop-iters.")
parser.add_argument(
    "--stop-iters",
    type=int,
    default=50,
    help="Number of iterations to train.")
parser.add_argument(
    "--stop-timesteps",
    type=int,
    default=100000,
    help="Number of timesteps to train.")
parser.add_argument(
    "--stop-reward",
    type=float,
    default=0.1,
    help="Reward at which we stop training.")
parser.add_argument(
    "--no-tune",
    action="store_true",
    help="Run without Tune using a manual train loop instead. In this case,"
         "use PPO without grid search and no TensorBoard.")
parser.add_argument(
    "--local-mode",
    action="store_true",
    help="Init Ray in local mode for easier debugging.")


def print_tree(info):

    episode = info["episode"]
    print(f"last info for: {episode.last_info_for()}")
    print(f"last info for: {episode}")
    info = episode.last_info_for("0")
    TreeUtils.print_tree_by_level(info["root"])
    save_tree_to_file(info["root"])

def save_tree_to_file(root):

    jsonStr = json.dumps(root.__dict__)
    print(jsonStr)


if __name__ == "__main__":
    args = parser.parse_args()
    print(f"Running with following CLI options: {args}")

    ray.init(local_mode=args.local_mode)
    ModelCatalog.register_custom_model('woodblock_action_masking_model',
                                       WoodBlockActionMaskModel)

    config = {
        "env": WoodBlockEnvMultiAgent,  # or "corridor" if registered above
        "env_config": {
            "custom_config": AppConfig('../../../../config/qdTreeConfig.json'),
        },
        # Use GPUs iff `RLLIB_NUM_GPUS` env var set to > 0.
        "num_gpus": int(os.environ.get("RLLIB_NUM_GPUS", "0")),
        "model": {
            "custom_model": "woodblock_action_masking_model",
            "fcnet_hiddens": [512, 512],
            "fcnet_activation": "relu",
            "vf_share_layers": True,
        },
        "lr": grid_search([1e-2, 1e-4, 1e-6]),  # try different lrs
        "num_workers": 1,  # parallelism
        "framework": args.framework,
        "log_level": "DEBUG",
    }

    stop = {
        "training_iteration": args.stop_iters,
        "timesteps_total": args.stop_timesteps,
        "episode_reward_mean": args.stop_reward,
    }

    ppo_config = ppo.DEFAULT_CONFIG.copy()
    ppo_config.update(config)
    # use fixed learning rate instead of grid search (needs tune)
    ppo_config["lr"] = 1e-3

    # ppo_config["callbacks"] = {"on_episode_end": tune.function(print_tree)}

    if args.no_tune:
        # manual training with train loop using PPO and fixed learning rate
        if args.run != "PPO":
            raise ValueError("Only support --run PPO with --no-tune.")
        print("Running manual train loop without Ray Tune.")
        ppo_config = ppo.DEFAULT_CONFIG.copy()
        ppo_config.update(config)
        # use fixed learning rate instead of grid search (needs tune)
        ppo_config["lr"] = 1e-3
        # ppo_config["callbacks"] = {"on_episode_end": tune.function(print_tree)}
        trainer = ppo.PPOTrainer(config=ppo_config, env=WoodBlockEnvMultiAgent)
        # run manual training loop and print results after each iteration
        for _ in range(args.stop_iters):
            print("Start training")
            result = trainer.train()
            print("Stop training")
            print(pretty_print(result))
            # stop training of the target train steps or reward are reached
            if result["timesteps_total"] >= args.stop_timesteps or \
                    result["episode_reward_mean"] >= args.stop_reward:
                break
    else:
        # automated run with Tune and grid search and TensorBoard
        print("Training automatically with Ray Tune")
        results = tune.run("PPO", config=ppo_config, stop=stop)

        if args.as_test:
            print("Checking if learning goals were achieved")
            check_learning_achieved(results, args.stop_reward)

    ray.shutdown()
