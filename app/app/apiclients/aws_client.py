import yaml


class AWSClientHelper:
    @staticmethod
    async def load_config(filepath: str):
        with open(filepath) as file:
            config_dict = yaml.safe_load(file)
            return config_dict
