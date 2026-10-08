import pandas as pd
import pytest


@pytest.fixture
def music_cycle_time(base_time):
    """A recent 06 UTC model cycle, formatted for native MUSIC parameters."""
    return (base_time + pd.Timedelta(hours=6)).strftime("%Y%m%d%H%M%S")
