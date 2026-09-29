"""Shared fixtures and collection policy for the test suite."""

from pathlib import Path

import pandas as pd
import pytest

from .fixtures.clients import FakeCMADaaSClient
from .fixtures.protobuf import (
    make_array2d_response,
    make_grid_array2d_response,
)


def pytest_collection_modifyitems(config, items):
    """Classify tests by their top-level directory."""
    tests_root = Path(__file__).parent
    for item in items:
        relative_path = Path(item.path).relative_to(tests_root)
        if relative_path.parts and relative_path.parts[0] == "integration":
            item.add_marker(pytest.mark.integration)
            if not any(item.iter_markers(name="smoke")) and not any(
                item.iter_markers(name="extended")
            ):
                item.add_marker(pytest.mark.extended)
        elif relative_path.parts and relative_path.parts[0] == "unit":
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def synthetic_time() -> pd.Timestamp:
    return pd.Timestamp("2026-01-02 00:00:00")


@pytest.fixture
def synthetic_time_range(synthetic_time: pd.Timestamp) -> pd.Interval:
    return pd.Interval(
        synthetic_time,
        synthetic_time + pd.Timedelta(hours=6),
        closed="both",
    )


@pytest.fixture
def synthetic_station_rows():
    return [
        {
            "Station_Id_C": "FAKE001",
            "Lat": 30.0,
            "Lon": 110.0,
            "TEM": 280.0,
        },
        {
            "Station_Id_C": "FAKE002",
            "Lat": 31.0,
            "Lon": 111.0,
            "TEM": 281.5,
        },
    ]


@pytest.fixture
def synthetic_grid():
    return {
        "latitude": [30.0, 31.0],
        "longitude": [110.0, 111.0, 112.0],
        "values": [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]],
        "name": "synthetic_temperature",
        "units": "K",
    }


@pytest.fixture
def synthetic_array2d():
    return make_array2d_response()


@pytest.fixture
def synthetic_grid_array2d():
    return make_grid_array2d_response()


@pytest.fixture
def fake_client(synthetic_array2d):
    return FakeCMADaaSClient(synthetic_array2d)


@pytest.fixture
def fake_grid_client(synthetic_grid_array2d):
    return FakeCMADaaSClient(synthetic_grid_array2d)
