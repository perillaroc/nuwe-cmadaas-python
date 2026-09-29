import pytest
import pandas as pd


@pytest.fixture
def end_date():
    return pd.Timestamp.now().normalize()
