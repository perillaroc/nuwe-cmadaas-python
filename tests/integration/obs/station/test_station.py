"""Manifest-backed station cases for ordinary and latest-time queries."""

import pandas as pd
import pytest

from nuwe_cmadaas.obs import retrieve_obs_station

from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize(
    "case", case_parameters("obs_station") + case_parameters("obs_station_latest")
)
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    kwargs["client"] = request.getfixturevalue("real_client")
    kwargs["strict"] = True
    table = retrieve_obs_station(**kwargs)

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataframe"
    assert isinstance(table, pd.DataFrame)
    if expected["nonempty"]:
        assert not table.empty
    columns = resolve_case_value(expected["columns"], dataset, request)
    assert set(columns).issubset(table.columns)
    if expected.get("metadata_interface_id"):
        assert table.attrs["interface_id"] == case["interface_id"]
    if "count" in kwargs:
        assert len(table) <= kwargs["count"]
    if "station_matches" in expected:
        station_id = resolve_case_value(expected["station_matches"], dataset, request)
        assert table["Station_Id_C"].astype(str).eq(str(station_id)).all()
    if "station_in" in expected:
        station_ids = resolve_case_value(expected["station_in"], dataset, request)
        assert table["Station_Id_C"].astype(str).isin(
            [str(station_id) for station_id in station_ids]
        ).all()
    if "station_between" in expected:
        minimum, maximum = resolve_case_value(expected["station_between"], dataset, request)
        stations = table["Station_Id_C"].astype(str)
        assert stations.between(str(minimum), str(maximum)).all()
    if "coordinates_within" in expected:
        region = resolve_case_value(expected["coordinates_within"], dataset, request)
        latitudes = pd.to_numeric(table["Lat"], errors="raise")
        longitudes = pd.to_numeric(table["Lon"], errors="raise")
        assert latitudes.between(
            min(region["start_latitude"], region["end_latitude"]),
            max(region["start_latitude"], region["end_latitude"]),
        ).all()
        assert longitudes.between(
            min(region["start_longitude"], region["end_longitude"]),
            max(region["start_longitude"], region["end_longitude"]),
        ).all()
