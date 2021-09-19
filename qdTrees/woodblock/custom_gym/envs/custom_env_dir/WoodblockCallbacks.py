from typing import Dict

from ray.rllib import RolloutWorker
from ray.rllib.agents import DefaultCallbacks
from ray.rllib.env import BaseEnv
from ray.rllib.evaluation import MultiAgentEpisode
from ray.rllib.policy import Policy


class WoodblockCallbacksClass(DefaultCallbacks):

    # def on_episode_end(self, worker: RolloutWorker, base_env: BaseEnv,
    #                    policies: Dict[str, Policy], episode: MultiAgentEpisode,
    #                    **kwargs):
    #     episode.custom_metrics['unormScore'] = episode._agent_to_last_info['agent0']['unormScore']
    #     episode.custom_metrics['someOtherData'] = episode._agent_to_last_info['agent0']['someOtherData']

    # def on_episode_end(self, worker, base_env,
    #                    episode, **kwargs):
    #     print(f"last info for: {episode.last_info_for()}")
    #     return

    def on_episode_end(self, *, worker: RolloutWorker, base_env: BaseEnv,
                       policies: Dict[str, Policy], episode: MultiAgentEpisode,
                       env_index: int, **kwargs):

        print(f"last info for: {episode.last_info_for()}")
