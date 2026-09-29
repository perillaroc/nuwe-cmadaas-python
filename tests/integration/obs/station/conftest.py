import pytest
import pandas as pd


@pytest.fixture
def start_date():
    """Station data uses yesterday's date, as in the original online tests."""
    return (pd.Timestamp.now() - pd.offsets.Day()).normalize()


@pytest.fixture
def end_date():
    return pd.Timestamp.now().normalize()


@pytest.fixture
def time_list():
    today = pd.Timestamp.now().normalize()
    return [today - pd.offsets.Day(), today]


@pytest.fixture
def start_station_id():
    return "53592"


@pytest.fixture
def end_station_id():
    return "54511"


@pytest.fixture
def station_id():
    return "54533"  # Beijing
