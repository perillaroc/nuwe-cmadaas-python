"""Every cataloged upper-air case must reach its declared public interface."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.obs import retrieve_obs_upper_air
from tests.fixtures import FakeCMADaaSClient, make_array2d_response
from tests.integration.case_registry import load_cases, resolve_case_value


pytestmark = pytest.mark.unit

FAMILIES = {
    "obs_upper", "obs_upper_gps", "obs_upper_light", "obs_upper_ard",
    "obs_upper_latest",
}
PROFILE = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "integration/profiles.example.yaml")
    .read_text(encoding="utf-8")
)


class SyntheticRequest:
    def getfixturevalue(self, name):
        base_time = pd.Timestamp("2026-01-02")
        return {
            "base_time": base_time,
            "short_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(hours=1), closed="both"
            ),
            "latest_delta": pd.Timedelta(hours=1),
            "flight_height_range": pd.Interval(0, 15000, closed="both"),
        }[name]


@pytest.mark.parametrize(
    "case", [case for case in load_cases() if case["family"] in FAMILIES],
    ids=lambda case: case["case_id"],
)
def test_upper_air_case_reaches_declared_interface(case):
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_array2d_response())

    retrieve_obs_upper_air(client=client, **kwargs)

    assert len(client.calls) == 1
    interface_id, params = client.calls[0]
    assert interface_id == case["interface_id"]
    if interface_id in {
        "getUparGpsEleByTimeAndStaID",
        "getUparGpsEleInRectByTime",
    }:
        assert "dataCode" not in params
    else:
        assert params["dataCode"] == dataset["data_code"]
    if "time_range" in case["query_features"]:
        assert "timeRange" in params
    if "station" in case["query_features"]:
        assert "staIds" in params
    if "level_press" in case["query_features"]:
        assert "pLayers" in params
    if "level_height_range" in case["query_features"]:
        assert params["minFLayer"] == 0
        assert params["maxFLayer"] == 15000
