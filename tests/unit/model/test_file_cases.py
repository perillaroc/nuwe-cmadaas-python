"""Cataloged NAFP file cases and request-before-network rejection."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface
from nuwe_cmadaas.model import download_model_file
from tests.fixtures import FakeCMADaaSClient, make_array2d_response, make_files_info_response
from tests.integration.case_registry import load_cases, resolve_case_value


pytestmark = pytest.mark.unit
PROFILE = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "integration/profiles.example.yaml")
    .read_text(encoding="utf-8")
)
CYCLE = (pd.Timestamp.now() - pd.Timedelta(days=3)).normalize() + pd.Timedelta(hours=6)
RANGE = pd.Interval(CYCLE, CYCLE + pd.Timedelta(hours=1), closed="both")
RECT = {
    "type": "rect", "start_longitude": 115.0, "end_longitude": 116.0,
    "start_latitude": 40.0, "end_latitude": 39.0,
}
EXPECTED = {
    "MF-003": ("getNafpFileByTime", {"time"}),
    "MF-004": ("getNafpFileByTimeRange", {"time_range"}),
    "MF-008": ("getNafpFileByElementAndTime", {"element", "time"}),
    "MF-009": ("getNafpFileByElementAndTimeRange", {"element", "time_range"}),
    "MF-010": ("getNafpFileByElementAndTimeAndLevel", {"element", "level", "time"}),
    "MF-012": ("getNafpFileByElementAndTimeAndValidtime", {"element", "time", "valid_time"}),
    "MF-019": ("getNafpFileByElementAndTimeAndLevelAndValidtime", {"element", "level", "time", "valid_time"}),
}
REMOVED = [
    (), ("element",), ("level",), ("level", "time"),
    ("level", "time_range"), ("element", "level", "time_range"),
    ("element", "time_range", "valid_time"), ("region",),
    ("region", "time"), ("region", "time_range"),
    ("element", "region", "time"), ("element", "region", "time_range"),
]


class SyntheticRequest:
    def getfixturevalue(self, name):
        return {
            "model_file_cycle_time": CYCLE,
            "model_file_cycle_time_range": RANGE,
            "online_output_dir": Path("/tmp/synthetic-model-files"),
        }[name]


def test_model_file_cases_cover_cataloged_registry():
    cases = load_cases("model_file")
    assert {case["case_id"] for case in cases} == set(EXPECTED)
    assert {
        (case["interface_id"], frozenset(case["query_features"])) for case in cases
    } == {(interface_id, frozenset(features)) for interface_id, features in EXPECTED.values()}
    assert len(cases) == len(EXPECTED)


@pytest.mark.parametrize("case_id", EXPECTED)
def test_model_file_case_reaches_exact_interface_and_parameters(case_id):
    case = next(case for case in load_cases("model_file") if case["case_id"] == case_id)
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_files_info_response())

    download_model_file(**kwargs, client=client)

    features = set(case["query_features"])
    params = {"dataCode": dataset["data_code"]}
    if "time" in features:
        params["time"] = CYCLE.strftime("%Y%m%d%H%M%S")
    if "time_range" in features:
        left = CYCLE.strftime("%Y%m%d%H%M%S")
        right = (CYCLE + pd.Timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        params["timeRange"] = f"[{left},{right}]"
    if "element" in features:
        params.update(fcstEle="TEM", levelType="103")
    if "level" in features:
        params["fcstLevel"] = "2"
    if "valid_time" in features:
        params["validTime"] = "24"
    if "count" in kwargs:
        params["limitCnt"] = "1"
    assert case["interface_id"] == EXPECTED[case_id][0]
    assert client.calls == [(EXPECTED[case_id][0], params)]


@pytest.mark.parametrize("features", REMOVED)
def test_removed_model_file_combinations_reject_before_request(features):
    kwargs = {"data_code": "SYNTHETIC_MODEL", "output_dir": Path("/tmp/synthetic-model-files")}
    if "element" in features:
        kwargs.update(parameter="TEM", level_type="103")
    if "level" in features:
        kwargs.update(level_type="103", level=2)
    if "time" in features:
        kwargs["start_time"] = CYCLE
    if "time_range" in features:
        kwargs["start_time"] = RANGE
    if "valid_time" in features:
        kwargs["forecast_time"] = "24h"
    if "region" in features:
        kwargs["region"] = RECT
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        download_model_file(**kwargs, client=client)

    assert client.calls == []


def test_catalog_required_level_type_is_checked_before_request():
    client = FakeCMADaaSClient(make_files_info_response())
    with pytest.raises(ValueError, match="requires parameters: levelType"):
        download_model_file(
            "SYNTHETIC_MODEL", parameter="TEM", start_time=CYCLE, client=client,
        )
    assert client.calls == []


@pytest.mark.parametrize("count", [0, -1, True, 1.5])
def test_model_file_count_rejects_invalid_values_before_request(count):
    client = FakeCMADaaSClient(make_files_info_response())
    with pytest.raises(ValueError, match="count must be a positive integer"):
        download_model_file("SYNTHETIC_MODEL", start_time=CYCLE, count=count, client=client)
    assert client.calls == []


def test_model_file_count_rejects_interfaces_without_catalog_limit():
    client = FakeCMADaaSClient(make_files_info_response())
    with pytest.raises(ValueError, match="count is supported only"):
        download_model_file(
            "SYNTHETIC_MODEL", parameter="TEM", level_type="103",
            start_time=CYCLE, count=1, client=client,
        )
    assert client.calls == []


def test_latest_time_case_uses_array2d_and_gfs_analysis():
    case, = load_cases("model_file_latest")
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(
        make_array2d_response(rows=[[CYCLE.strftime("%Y%m%d%H%M%S")]], element_names=["Datetime"])
    )

    response = client.callAPI_to_array2D(**kwargs)

    assert case["case_id"] == "MFL-001"
    assert resolve_interface("model_file_latest", ()).return_type == "array_2d"
    assert case["public_function"] == "CMADaaSClient.callAPI_to_array2D"
    assert client.calls == [
        ("getNafpLatestTime", {
            "dataCode": "NAFP_ANA_FTM_GRAPES_GFS_NEHE", "latestTime": "72",
        })
    ]
    assert response.to_pandas()["Datetime"].tolist() == [CYCLE.strftime("%Y%m%d%H%M%S")]
