"""Shared fixtures and collection policy for the test suite."""

import os
from pathlib import Path

import pandas as pd
import pytest
import yaml

from .fixtures.clients import FakeCMADaaSClient
from .fixtures.protobuf import (
    make_array2d_response,
    make_grid_array2d_response,
)


def pytest_collection_modifyitems(config, items):
    """Classify the pre-existing service-backed tests as integrations."""
    tests_root = Path(__file__).parent
    for item in items:
        relative_path = Path(item.path).relative_to(tests_root)
        if relative_path.parts and relative_path.parts[0] in {"obs", "model"}:
            item.add_marker(pytest.mark.integration)


def _integration_config_is_available() -> bool:
    config_path = os.environ.get("CEDARKIT_CONFIG")
    if config_path is None:
        config_path = Path.home() / ".config/cedarkit.yaml"

    try:
        from nuwe_cmadaas.config import load_cmadaas_config

        config = load_cmadaas_config(config_path)
        auth = config["auth"]
        server = config["server"]
        required_values = (
            auth["user"],
            auth["password"],
            server["music_server"],
            server["music_port"],
            server["music_ServiceId"],
        )
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError):
        return False

    return all(str(value).strip() for value in required_values)


@pytest.fixture(autouse=True)
def skip_integration_without_config(request):
    """Skip service tests early when no usable external config is present."""
    if request.node.get_closest_marker("integration") is not None:
        if not _integration_config_is_available():
            pytest.skip(
                "CMADaaS integration credentials are not configured; "
                "set CEDARKIT_CONFIG to run online tests"
            )


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
