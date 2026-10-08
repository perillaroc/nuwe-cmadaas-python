"""Recent forecast cycles for bounded model-file requests."""

import pandas as pd
import pytest


@pytest.fixture
def model_file_cycle_time(base_time):
    return base_time + pd.Timedelta(hours=6)


@pytest.fixture
def model_file_cycle_time_range(model_file_cycle_time):
    return pd.Interval(
        model_file_cycle_time,
        model_file_cycle_time + pd.Timedelta(hours=1),
        closed="both",
    )
