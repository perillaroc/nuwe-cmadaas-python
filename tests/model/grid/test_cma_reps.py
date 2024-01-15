import pandas as pd

from nuwe_cmadaas.model import retrieve_model_grid


REPS_CONTROL_NAME = "NAFP_GRAPESREPS_FOR_FTM_CHN"
REPS_MEMBER_NAME = "NAFP_GRAPESREPS_FOR_FTM_DIS_CHN"


def test_control_field(start_date):
    field = retrieve_model_grid(
        REPS_CONTROL_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter="TEM",
        level_type=100,
        level=850,
        number=0,
    )

    assert field is not None


def test_member_field(start_date):
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter="TEM",
        level_type=100,
        level=850,
        number=10,
    )

    assert field is not None
