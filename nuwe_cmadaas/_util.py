import pandas as pd

from .music import CMADaaSClient
from ._config import load_cmadaas_config


def _get_client(config_file) -> CMADaaSClient:
    config = load_cmadaas_config(config_file)
    client = CMADaaSClient(config=config)
    return client


def _get_time_string(time: pd.Timestamp) -> str:
    return time.strftime("%Y%m%d%H%M%S")


def _get_time_range_string(time_interval: pd.Interval) -> str:
    left = "[" if time_interval.closed_left else ")"
    start = _get_time_string(time_interval.left)
    right = "[" if time_interval.closed_right else ")"
    end = _get_time_string(time_interval.right)
    return f"{left}{start},{end}{right}"
