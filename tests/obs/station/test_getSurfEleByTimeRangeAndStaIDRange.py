"""
按时间段、站号段检索地面数据要素

getSurfEleByTimeRangeAndStaIDRange
"""

import pandas as pd

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date, end_date, start_station_id, end_station_id):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=pd.Interval(
            start_date, start_date + pd.Timedelta(hours=6),
            closed="left",
        ),
        station=(start_station_id, end_station_id),
    )
    print(table)
