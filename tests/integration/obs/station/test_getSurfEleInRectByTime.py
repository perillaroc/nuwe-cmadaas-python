"""
按时间、经纬度范围检索地面数据要素

getSurfEleInRectByTime
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date, end_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=[start_date, end_date],
        region={
            "type": "rect",
            "start_longitude": 115.7,
            "end_longitude": 117.4,
            "start_latitude": 41.6,
            "end_latitude": 39.4,
        }
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0
