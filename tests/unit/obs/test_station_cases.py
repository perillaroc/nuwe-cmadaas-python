"""Check every station manifest entry through the public function offline."""

import pandas as pd
import pytest

from nuwe_cmadaas.obs import retrieve_obs_station
from tests.fixtures import FakeCMADaaSClient, make_array2d_response
from tests.integration.case_registry import load_cases, resolve_case_value


DATASET = {
    "data_code": "SURF_CHN_MUL_HOR",
    "elements": "Station_Id_C,Lat,Lon,TEM",
    "station_id": "FAKE001",
    "station_ids": ["FAKE001", "FAKE002"],
    "station_range": ["FAKE001", "FAKE002"],
    "rect_station_id": "FAKE001",
    "admin_station_id": "FAKE001",
    "basin_station_id": "FAKE001",
    "station_level": "011",
    "region": {
        "type": "rect", "start_longitude": 110.0, "end_longitude": 110.2,
        "start_latitude": 30.0, "end_latitude": 30.2,
    },
    "admin_region": {"type": "region", "admin_codes": "110000"},
    "basin_region": {"type": "basin", "basin_codes": "CJLY"},
    "max_rows": 20,
}


class FixedRequest:
    def getfixturevalue(self, name):
        base_time = pd.Timestamp("2026-01-02 00:00:00")
        return {
            "station_base_time": base_time,
            "station_short_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(hours=1), closed="both"
            ),
            "station_hour_left_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(hours=1), closed="left"
            ),
            "station_six_hour_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(hours=6), closed="left"
            ),
            "station_day_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(days=1), closed="left"
            ),
            "station_time_list": [base_time, base_time + pd.Timedelta(days=1)],
            "latest_delta": pd.Timedelta(hours=1),
        }[name]


@pytest.mark.parametrize(
    "case",
    [
        c for c in load_cases()
        if c["implemented"] and c["family"] in {"obs_station", "obs_station_latest"}
    ],
    ids=lambda case: case["case_id"],
)
def test_station_case_uses_registered_interface_and_query(case):
    dataset = {**DATASET, "data_code": "SURF_CHN_MUL_HOR_N"} if case["family"].endswith("latest") else DATASET
    if case["profile_key"] == "obs_station_climate_hourly":
        dataset = {
            **DATASET,
            "data_code": "SURF_CLI_CHN_HOR_TEM_1991_2020",
            "order": "Station_Id_C:asc",
        }
    kwargs = resolve_case_value(case["public_kwargs"], dataset, FixedRequest())
    client = FakeCMADaaSClient(make_array2d_response())
    retrieve_obs_station(**kwargs, client=client, strict=True)

    assert len(client.calls) == 1
    interface_id, params = client.calls[0]
    assert interface_id == case["interface_id"]
    assert params["dataCode"] == dataset["data_code"]
    features = set(case["query_features"])
    if case["family"].endswith("latest"):
        assert params["latestTime"] == "1"
        return

    assert params["elements"] == dataset["elements"]
    if case["profile_key"] == "obs_station_climate_hourly":
        assert params["orderby"] == "Station_Id_C:asc"
        assert not {"times", "timeRange", "latestTime"}.intersection(params)
    if "count" in case["public_kwargs"]:
        assert params["limitCnt"] == dataset["max_rows"]
    else:
        assert "limitCnt" not in params
    if "time" in features:
        requested_time = resolve_case_value(case["public_kwargs"]["time"], dataset, FixedRequest())
        assert params["times"] == (
            "20260102000000,20260103000000"
            if isinstance(requested_time, list) else "20260102000000"
        )
    if "time_range" in features:
        fixture = case["public_kwargs"]["time"]["fixture"]
        assert params["timeRange"] == {
            "station_short_time_range": "[20260102000000,20260102010000]",
            "station_hour_left_time_range": "[20260102000000,20260102010000)",
            "station_six_hour_time_range": "[20260102000000,20260102060000)",
            "station_day_time_range": "[20260102000000,20260103000000)",
        }[fixture]
    if "station" in features:
        stations = resolve_case_value(case["public_kwargs"]["station"], dataset, FixedRequest())
        assert params["staIds"] == (
            ",".join(stations) if isinstance(stations, list) else stations
        )
    if "station_range" in features:
        assert (params["minStaId"], params["maxStaId"]) == tuple(dataset["station_range"])
    if "station_level" in features:
        assert params["staLevels"] == dataset["station_level"]
    if "region_rect" in features:
        assert (params["minLat"], params["minLon"], params["maxLat"], params["maxLon"]) == (
            "30.0", "110.0", "30.2", "110.2"
        )
    if "region_region" in features:
        assert params["adminCodes"] == "110000"
    if "region_basin" in features:
        assert params["basinCodes"] == "CJLY"


def test_all_deleted_station_scenarios_have_implemented_manifest_cases():
    expected = {
        "station/test_getSurfEleByTime.py::test_hourly",
        "station/test_getSurfEleByTimeAndStaID.py::test_hourly_station_list",
        "station/test_getSurfEleByTimeAndStaID.py::test_hourly_station",
        "station/test_getSurfEleByTimeAndStaIdRange.py::test_hourly",
        "station/test_getSurfEleByTimeRange.py::test_hourly",
        "station/test_getSurfEleByTimeRangeAndStaID.py::test_hourly",
        "station/test_getSurfEleByTimeRangeAndStaID.py::test_hourly_station_id",
        "station/test_getSurfEleByTimeRangeAndStaIDRange.py::test_hourly",
        "station/test_getSurfEleInBasinByTime.py::test_hourly",
        "station/test_getSurfEleInBasinByTimeRange.py::test_hourly",
        "station/test_getSurfEleInRectByTime.py::test_hourly",
        "station/test_getSurfEleInRectByTimeRange.py::test_hourly",
        "station/test_getSurfEleInRegionByTime.py::test_hourly",
        "station/test_getSurfEleInRegionByTimeRange.py::test_hourly",
        "station/test_getSurfLatestTime.py::test_hourly",
    }
    cases = [
        case for case in load_cases()
        if case["family"] in {"obs_station", "obs_station_latest"}
    ]
    migrated = {
        legacy_test for case in cases if case["implemented"]
        for legacy_test in case.get("legacy_tests", [])
    }
    assert migrated == expected
