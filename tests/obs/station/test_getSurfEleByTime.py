"""
按时间检索地面数据要素

getSurfEleByTime
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date, end_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=[start_date, end_date]
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0
    return
