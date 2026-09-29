"""
按时间、要素获取实况格点场要素

getSurfEleGridInRectByTime
"""
import xarray as xr

from nuwe_cmadaas.obs import retrieve_obs_grid


def test_cmpas_chn_1km_rt(start_date):
    parameter = "PRE"

    data_code = "SURF_CMPAS_CHN_1KM_RT"

    field = retrieve_obs_grid(
        data_code,
        parameter=parameter,
        time=start_date,
        region=dict(
            type="rect",
            start_longitude=115.7,
            end_longitude=117.4,
            start_latitude=41.6,
            end_latitude=39.4,
        )
    )

    assert isinstance(field, xr.DataArray)
