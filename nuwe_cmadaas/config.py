import os
from typing import Optional, Dict, Union, TypedDict
from pathlib import Path

import yaml


CONFIG_ENV_NAME = "CEDARKIT_CONFIG"


class AuthItem(TypedDict):
    user: str
    password: str


class ServerItem(TypedDict):
    music_server: str
    music_port: int
    music_connTimeout: int
    music_readTimeout: int
    music_ServiceId: int


class CMADaasConfig(TypedDict):
    auth: AuthItem
    server: ServerItem


def load_cmadaas_config(file_path: Optional[Union[str, Path]] = None) -> CMADaasConfig:
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
