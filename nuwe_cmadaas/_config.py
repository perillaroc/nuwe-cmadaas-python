import typing
import os
import pathlib

import yaml


def load_cmadaas_config(file_path: typing.Optional[str] = None):
    path = _get_cmadaas_config_path(file_path)
    with open(path) as f:
        config = yaml.safe_load(f)
        return config["cmadaas"]


def _get_cmadaas_config_path(file_path: typing.Optional[str] = None):
    if file_path is None:
        if "NWPC_OPER_CONFIG" in os.environ:
            return os.environ["NWPC_OPER_CONFIG"]
        path = pathlib.Path(pathlib.Path.home(), ".config/nwpc-oper/config.yaml")
        return path
    else:
        return file_path

