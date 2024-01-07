import pandas as pd

from .music import CMADaaSClient
from .config import load_cmadaas_config


def get_client(config_file) -> CMADaaSClient:
    config = load_cmadaas_config(config_file)
    client = CMADaaSClient(config=config)
    return client


def get_time_string(time: pd.Timestamp) -> str:
    return time.strftime("%Y%m%d%H%M%S")


def get_time_range_string(time_interval: pd.Interval) -> str:
    left = "[" if time_interval.closed_left else ")"
    start = get_time_string(time_interval.left)
    right = "[" if time_interval.closed_right else ")"
    end = get_time_string(time_interval.right)
    return f"{left}{start},{end}{right}"
