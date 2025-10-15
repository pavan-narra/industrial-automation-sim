import yaml, csv, os

class ConfigManager:
    def __init__(self, config_path="configs/alarms.yaml"):
        self.config_path = config_path
        self.config = {}

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        return self.config

    def load_io_map(self, io_path="configs/io_map.csv"):
        with open(io_path, 'r') as f:
            return list(csv.DictReader(f))
