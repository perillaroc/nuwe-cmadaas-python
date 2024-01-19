from nuwe_cmadaas.obs import retrieve_obs_grid


def test_getSurfEleGridByTime(start_date):
    parameter = "PRE"

    data_code = "SURF_CMPAS_CHN_1KM_RT"

    field = retrieve_obs_grid(
        data_code,
        parameter=parameter,
        time=start_date,
    )

    assert field is not None
