import pytest
import pandas as pd


# These are explicitly online integration tests. Dynamic dates keep the
# service-backed examples aligned with data currently available on CMADaaS.
@pytest.fixture
def start_date():
    s = (pd.Timestamp.now() - pd.offsets.Day()).normalize() - pd.Timedelta(days=2)
    return s


@pytest.fixture
def end_date():
    s = pd.Timestamp.now().normalize()
    return s
