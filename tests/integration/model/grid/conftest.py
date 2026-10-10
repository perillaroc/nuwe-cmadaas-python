import pytest
import pandas as pd


@pytest.fixture
def model_cycle_time(base_time):
    return base_time + pd.Timedelta(hours=6)


@pytest.fixture
def start_time_for_reps():
    """Use the previous day's 06 cycle while recent REPS grids are available."""
    return (pd.Timestamp.now() - pd.Timedelta(days=1)).normalize() + pd.Timedelta(hours=6)


@pytest.fixture
def future_start_date():
    return (pd.Timestamp.now() - pd.offsets.Day()).normalize() + pd.Timedelta(days=365)


@pytest.fixture
def end_date():
    return pd.Timestamp.now().normalize()


@pytest.fixture
def invalid_forecast_time():
    forecast_time = pd.Timedelta(hours=888)
    return forecast_time


@pytest.fixture
def non_exist_ens_member_number():
    return 99
