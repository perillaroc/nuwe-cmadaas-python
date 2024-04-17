import pandas as pd
import xarray as xr

from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.music import MusicError


REPS_CONTROL_NAME = "NAFP_GRAPESREPS_FOR_FTM_CHN"
REPS_MEMBER_NAME = "NAFP_GRAPESREPS_FOR_FTM_DIS_CHN"

TEMPERATURE_NAME_FOR_CMADAAS = "TEM"


def test_control_field(start_date):
    field = retrieve_model_grid(
        REPS_CONTROL_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=850,
        number=0,
    )

    assert isinstance(field, xr.DataArray)


def test_member_field(start_date):
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=850,
        number=10,
    )

    assert isinstance(field, xr.DataArray)


def test_control_field_future_date(future_start_date):
    field = retrieve_model_grid(
        REPS_CONTROL_NAME,
        start_time=future_start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=850,
        number=0,
    )

    assert isinstance(field, MusicError)
    assert field.code == -1
    assert field.message == "query success , but no record in database. detail: Query Success,but no record is in database"


def test_control_field_non_exist_forecast_time(start_date, invalid_forecast_time):
    field = retrieve_model_grid(
        REPS_CONTROL_NAME,
        start_time=start_date,
        forecast_time=invalid_forecast_time,
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=850,
        number=0,
    )

    assert isinstance(field, MusicError)
    assert field.code == -9002
    assert field.message == ". detail: The input parameters are not within the range of datasets"


def test_member_field_non_exist_member(start_date, non_exist_ens_member_number):
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=850,
        number=non_exist_ens_member_number,
    )

    assert isinstance(field, MusicError)
    assert field.code == -9002
    assert field.message == ". detail: The input parameters are not within the range of datasets"


def test_member_field_non_exist_parameter(start_date, non_exist_ens_member_number):
    parameter = "NON_EXIST"
    level = 100
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=parameter,
        level_type=level,
        level=850,
        number=non_exist_ens_member_number,
    )

    assert isinstance(field, MusicError)
    assert field.code == -3001
    assert field.message == f". detail: The fsctele:'{parameter}_{level}' is not config in {REPS_MEMBER_NAME}"


def test_member_field_non_exist_field(start_date, non_exist_ens_member_number):
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=103,
        level=100,
        number=non_exist_ens_member_number,
    )

    assert isinstance(field, MusicError)
    assert field.code == -9002
    assert field.message == ". detail: The input parameters are not within the range of datasets"


def test_member_field_non_exist_level(start_date, non_exist_ens_member_number):
    field = retrieve_model_grid(
        REPS_MEMBER_NAME,
        start_time=start_date,
        forecast_time=pd.Timedelta(hours=24),
        parameter=TEMPERATURE_NAME_FOR_CMADAAS,
        level_type=100,
        level=851,
        number=non_exist_ens_member_number,
    )

    assert isinstance(field, MusicError)
    assert field.code == -9002
    assert field.message == ". detail: The input parameters are not within the range of datasets"
