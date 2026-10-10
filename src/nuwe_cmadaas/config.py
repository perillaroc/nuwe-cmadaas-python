import os
from typing import Optional, Dict, Union, TypedDict
from pathlib import Path

import yaml


CONFIG_ENV_NAME = "CEDARKIT_CONFIG"


class AuthItem(TypedDict):
    """Required auth.user/auth.password strings; an ordinary dict at runtime."""
    user: str
    password: str


class ServerItem(TypedDict):
    """Required MUSIC host, port, service node and timeout configuration keys."""
    music_server: str
    music_port: int
    music_connTimeout: int
    music_readTimeout: int
    music_ServiceId: int


class CMADaasConfig(TypedDict):
    """Inner CedarKit cmadaas mapping with required auth and server keys.

    TypedDict annotations guide type checking, without runtime validation.
    The YAML file has a cmadaas wrapper; this mapping does not.
    """
    auth: AuthItem
    server: ServerItem


def load_cmadaas_config(file_path: Optional[Union[str, Path]] = None) -> CMADaasConfig:
    """Read a CedarKit YAML file and return its cmadaas node.

    Parameters
    ----------
    file_path : str or pathlib.Path, optional
        Explicit YAML path. When None, use CEDARKIT_CONFIG if the variable
        exists, otherwise ~/.config/cedarkit.yaml. Relative paths use the
        process working directory; explicit strings do not expand ~.

    Returns
    -------
    CMADaasConfig
        Parsed cmadaas value, without validating its runtime schema or
        merging sources. Missing files, YAML parse failures and absent
        cmadaas keys propagate their native exceptions; no network request
        is performed and a failed explicit source does not fall back.
    """
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
