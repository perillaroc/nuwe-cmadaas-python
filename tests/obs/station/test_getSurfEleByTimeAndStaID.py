"""
按时间段、站号检索地面数据要素

getSurfEleByTimeRangeAndStaID
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly_station_list(start_date, end_date, start_station_id, end_station_id):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(start_date, end_date, closed="left"),
        station=[start_station_id, end_station_id]
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0


def test_hourly_station(start_date, end_date, station_id):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(start_date, end_date, closed="left"),
        station=station_id,
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0
