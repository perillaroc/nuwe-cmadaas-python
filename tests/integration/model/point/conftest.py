import pandas as pd
import pytest


@pytest.fixture
def model_point_cycle_time(base_time):
    return base_time + pd.Timedelta(hours=6)
