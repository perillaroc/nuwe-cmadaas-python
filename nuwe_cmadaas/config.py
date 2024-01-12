import os
from typing import Optional, Dict, Union
from pathlib import Path

import yaml


CONFIG_ENV_NAME = "CEDARKIT_CONFIG"


def load_cmadaas_config(file_path: Optional[str] = None) -> Dict:
    path = _get_cedarkit_config_path(file_path)
    with open(path) as f:
        config = yaml.safe_load(f)
        return config["cmadaas"]


def _get_cedarkit_config_path(file_path: Optional[Union[str, Path]] = None) -> Union[str, Path]:
    if file_path is None:
        if CONFIG_ENV_NAME in os.environ:
            return os.environ[CONFIG_ENV_NAME]
        path = Path(Path.home(), ".config/cedarkit.yaml")
        return path
    else:
        return file_path
