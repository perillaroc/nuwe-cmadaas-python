import pytest
import pandas as pd


@pytest.fixture
def start_date():
    s = (pd.Timestamp.now() - pd.offsets.Day()).normalize() - pd.Timedelta(days=2)
    return s


@pytest.fixture
def future_start_date():
    s = (pd.Timestamp.now() - pd.offsets.Day()).normalize() + pd.Timedelta(days=365)
    return s


@pytest.fixture
def end_date():
    s = pd.Timestamp.now().normalize()
    return s


@pytest.fixture
def invalid_forecast_time():
    forecast_time = pd.Timedelta(hours=888)
    return forecast_time


@pytest.fixture
def non_exist_ens_member_number():
    return 99
