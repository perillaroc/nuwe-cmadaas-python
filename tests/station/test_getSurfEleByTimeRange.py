"""
按时间段检索地面数据要素

getSurfEleByTimeRange
"""
import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(
            start_date,
            start_date + pd.Timedelta(hours=1),
            closed="left",
        ),
    )
    print(table)
