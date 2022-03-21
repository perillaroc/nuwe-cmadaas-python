"""
获取地面资料最新时次

getSurfLatestTime
"""

import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly():
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.to_timedelta("1h"),
    )
    print(table)
