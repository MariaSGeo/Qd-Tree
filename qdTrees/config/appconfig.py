import json
from collections import ChainMap


# used to get configuration values from the provided json
class AppConfig:
    def __init__(self, path="./qdTreeConfig.json"):
        self.config = {}
        with open(path, 'r') as f:
            self.config = json.load(f)

    def get_config(self, config_name, default=None):
        if default is None:
            return self.config.get(config_name)
        else:
            return self.config.get(config_name, default)

    def get_config_as_set(self, config_name, default=None):
        return set(self.get_config(config_name, default))

    def get_config_as_dict(self, config_name, default=None):
        return ChainMap(*self.get_config(config_name, default))

    def update_config(self, name, value):
        self.config[name] = value
