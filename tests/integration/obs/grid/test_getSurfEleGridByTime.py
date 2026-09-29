"""
按时间、要素获取实况格点场要素

getSurfEleGridByTime
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
    )

    assert isinstance(field, xr.DataArray)
