import yaml


def load_cmadaas_config(file_path):
    with open(file_path) as f:
        config = yaml.safe_load(f)
        return config["cmadaas"]
