from pathlib import Path
from typing import Dict

import yaml


DEFAULT_DATASETS_CONFIG_PATH = Path(Path(__file__).parent, "data/datasets")


def load_dataset_config(dataset_type: str) -> Dict:
    config_file_path = Path(DEFAULT_DATASETS_CONFIG_PATH, f"{dataset_type}.yaml")
    if not config_file_path.exists():
        raise FileNotFoundError(f"dataset file is not found: {config_file_path.absolute()}")

    with open(config_file_path, "r", encoding="utf-8") as f:
        dataset_config = yaml.safe_load(f)
        return dataset_config
