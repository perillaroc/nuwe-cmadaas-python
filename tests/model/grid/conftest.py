import pytest
import pandas as pd


@pytest.fixture
def start_date():
    s = (pd.Timestamp.now() - pd.offsets.Day()).normalize() - pd.Timedelta(days=2)
    return s


@pytest.fixture
def end_date():
    s = pd.Timestamp.now().normalize()
    return s
