"""
按时间段、地区检索地面要素数据

getSurfEleInRegionByTimeRange
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date, end_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(
            start_date, end_date,
            closed="left",
        ),
        region={
            "type": "region",
            "admin_codes": "110000"
        }
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0
