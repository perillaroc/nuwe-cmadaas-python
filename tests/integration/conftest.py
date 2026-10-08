"""Fixtures used only when service-backed tests execute."""

import os
from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.music import create_client


@pytest.fixture
def start_date():
    """Runtime base date for grid/model cases; station tests override it."""
    return (pd.Timestamp.now() - pd.offsets.Day()).normalize() - pd.Timedelta(days=2)


@pytest.fixture
def base_time(start_date):
    return start_date


@pytest.fixture
def station_base_time():
    """Station queries retain the original previous-day schedule."""
    return (pd.Timestamp.now() - pd.offsets.Day()).normalize()


@pytest.fixture
def station_short_time_range(station_base_time):
    return pd.Interval(
        station_base_time,
        station_base_time + pd.Timedelta(hours=1),
        closed="both",
    )


@pytest.fixture
def station_hour_left_time_range(station_base_time):
    return pd.Interval(
        station_base_time,
        station_base_time + pd.Timedelta(hours=1),
        closed="left",
    )


@pytest.fixture
def station_six_hour_time_range(station_base_time):
    return pd.Interval(
        station_base_time,
        station_base_time + pd.Timedelta(hours=6),
        closed="left",
    )


@pytest.fixture
def station_day_time_range(station_base_time):
    return pd.Interval(
        station_base_time,
        station_base_time + pd.Timedelta(days=1),
        closed="left",
    )


@pytest.fixture
def station_time_list(station_base_time):
    """Preserve the old station tests' previous-day/today list."""
    return [station_base_time, station_base_time + pd.Timedelta(days=1)]


@pytest.fixture
def short_time_range(base_time):
    return pd.Interval(base_time, base_time + pd.Timedelta(hours=1), closed="both")


@pytest.fixture
def flight_height_range(dataset_profile):
    lower, upper = dataset_profile("obs_upper_ard")["flight_height_bounds"]
    return pd.Interval(lower, upper, closed="both")


@pytest.fixture
def time_list(base_time):
    return [base_time, base_time + pd.Timedelta(hours=1)]


@pytest.fixture
def latest_delta():
    """Latest-time cases use a relative duration, not the ordinary base date."""
    return pd.Timedelta(hours=1)


@pytest.fixture(scope="session")
def integration_config():
    """Read credentials at execution time, without connecting to the service."""
    config_path = Path(
        os.environ.get("CEDARKIT_CONFIG") or Path.home() / ".config/cedarkit.yaml"
    ).expanduser()
    if not config_path.is_file():
        pytest.skip(
            "CMADaaS credentials are missing; set CEDARKIT_CONFIG "
            "to an existing CedarKit YAML config"
        )

    try:
        config = load_cmadaas_config(config_path)
        auth, server = config["auth"], config["server"]
        required_values = (
            auth["user"],
            auth["password"],
            server["music_server"],
            server["music_port"],
            server["music_ServiceId"],
        )
        if not all(value is not None and str(value).strip() for value in required_values):
            raise ValueError("required credential or server field is blank")
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        pytest.fail(f"Invalid CMADaaS config at {config_path}: {type(exc).__name__}")
    return config


@pytest.fixture(autouse=True)
def require_integration_config(integration_config):
    """Keep legacy service tests guarded until they use the shared client."""


@pytest.fixture(scope="session")
def integration_profile():
    """Load test-only dataset/capability values when a case requests them."""
    profile_path = os.environ.get("NUWE_CMADAAS_TEST_PROFILE")
    if not profile_path:
        pytest.skip("Test profile is missing; set NUWE_CMADAAS_TEST_PROFILE")
    path = Path(profile_path).expanduser()
    if not path.is_file():
        pytest.skip(f"Test profile is missing: {path}")
    try:
        with path.open(encoding="utf-8") as stream:
            profile = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        pytest.fail(f"Invalid test profile at {path}: {type(exc).__name__}")
    if not isinstance(profile, dict):
        pytest.fail(f"Invalid test profile at {path}: expected a mapping")
    return profile


@pytest.fixture
def dataset_profile(integration_profile):
    """Return an enabled dataset; unavailable optional datasets skip explicitly."""

    def get_dataset(key):
        dataset = integration_profile.get("datasets", {}).get(key)
        if not isinstance(dataset, dict) or not dataset.get("enabled", False):
            pytest.skip(f"Dataset capability is unavailable or disabled: {key}")
        return dataset

    return get_dataset


@pytest.fixture
def low_level_profile(integration_profile):
    """Return an enabled low-level method capability."""

    def get_method(method):
        capability = integration_profile.get("low_level", {}).get(method)
        if not isinstance(capability, dict) or not capability.get("enabled", False):
            pytest.skip(f"Low-level capability is unavailable or disabled: {method}")
        return capability

    return get_method


@pytest.fixture
def real_client(integration_config):
    """Construct a real client; authentication and request errors propagate."""
    return create_client(integration_config)


@pytest.fixture
def online_output_dir(tmp_path):
    """All service download cases should pass this path as output_dir."""
    return tmp_path
