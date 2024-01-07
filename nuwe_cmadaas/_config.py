import typing
import os
import pathlib

import yaml


CONFIG_ENV_NAME = "CEDARKIT_CONFIG"


def load_cmadaas_config(file_path: typing.Optional[str] = None):
    path = _get_cedarkit_config_path(file_path)
    with open(path) as f:
        config = yaml.safe_load(f)
        return config["cmadaas"]


def _get_cedarkit_config_path(file_path: typing.Optional[str] = None):
    if file_path is None:
        if CONFIG_ENV_NAME in os.environ:
            return os.environ[CONFIG_ENV_NAME]
        path = pathlib.Path(pathlib.Path.home(), ".config/cedarkit.yaml")
        return path
    else:
        return file_path
