import pytest
import pandas as pd


# These are explicitly online integration tests. Dynamic dates keep the
# service-backed examples aligned with data currently available on CMADaaS.
@pytest.fixture
def start_date():
    s = (pd.Timestamp.now() - pd.offsets.Day()).normalize()
    return s


@pytest.fixture
def end_date():
    s = pd.Timestamp.now().normalize()
    return s


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
