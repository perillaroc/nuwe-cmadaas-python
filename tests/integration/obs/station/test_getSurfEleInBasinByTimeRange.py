"""
按时间段、流域检索地面数据要素

getSurfEleInBasinByTimeRange
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(
            start_date, start_date + pd.Timedelta(hours=6),
            closed="left",
        ),
        region={
            "type": "basin",
            "basin_codes": "CJLY"
        },
    )
    assert isinstance(table, pd.DataFrame)
    assert table.shape[0] > 0
