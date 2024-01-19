"""
按时间段、经纬度范围检索地面要素资料

getSurfEleInRectByTimeRange
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
        region={
            "type": "rect",
            "start_longitude": 115.7,
            "end_longitude": 117.4,
            "start_latitude": 41.6,
            "end_latitude": 39.4,
        },
    )
    print(table)
