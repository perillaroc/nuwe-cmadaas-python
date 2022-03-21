"""
按时间、流域检索地面数据要素

getSurfEleInBasinByTime
"""

from nuwe_cmadaas.obs import retrieve_obs_station


def test_hourly(start_date, end_date):
    table = retrieve_obs_station(
        "SURF_CHN_MUL_HOR",
        time=[start_date, end_date],
        region={
            "type": "basin",
            "basin_codes": "CJLY"
        },
    )
    print(table)
