from gym.vector.utils import spaces
from ray.rllib.models.tf import TFModelV2, FullyConnectedNetwork
from ray.rllib.utils.framework import try_import_tf

tf1, tf, tfv = try_import_tf()


class WoodBlockActionMaskModel(TFModelV2):

    def __init__(self,
                 obs_space,
                 action_space,
                 num_outputs,
                 model_config,
                 name
                 # true_obs_shape,
                 # action_embed_size
                 ):

        super(WoodBlockActionMaskModel, self).__init__(obs_space,
                                                       action_space,
                                                       num_outputs,
                                                       model_config,
                                                       name)
        true_obs_shape = obs_space.original_space.spaces['state'].n
        action_embed_size = obs_space.original_space.spaces['avail_actions'].shape[0]
        self.action_embed_size = 1
        self.action_embed_model = FullyConnectedNetwork(spaces.Box(0, 1, shape=(true_obs_shape,)),
                                                        action_space,
                                                        action_embed_size,
                                                        model_config,
                                                        name + "_action_embedding")

        self.register_variables(self.action_embed_model.variables())

    def forward(self, input_dict, state, seq_lens):

        # Extract the available actions tensor from the observation.
        avail_actions = input_dict["obs"]["avail_actions"]
        action_mask = input_dict["obs"]["action_mask"]

        # Compute the predicted action embedding
        action_embedding, _ = self.action_embed_model({"obs": input_dict["obs"]["state"]})

        # Expand the model output to [BATCH, 1, EMBED_SIZE]. Note that the
        # avail actions tensor is of shape [BATCH, MAX_ACTIONS, EMBED_SIZE].
        intent_vector = tf.expand_dims(action_embedding, 1)

        # Batch dot product => shape of logits is [BATCH, MAX_ACTIONS].
        action_logits = tf.reduce_sum(avail_actions * intent_vector, axis=1)

        # vs in the official example its the following axis=2
        # action_logits = tf.reduce_sum(avail_actions * intent_vector, axis=2)

        # Mask out invalid actions (use tf.float32.min for stability)
        inf_mask = tf.maximum(tf.math.log(action_mask), tf.float32.min)

        return action_logits + inf_mask, state

    def value_function(self):
        return self.action_embed_model.value_function()
