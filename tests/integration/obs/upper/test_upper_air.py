"""Catalog-backed high-level upper-air queries against a real service."""

import pandas as pd
import pytest

from nuwe_cmadaas.obs import retrieve_obs_upper_air
from tests.integration.case_registry import case_parameters, resolve_case_value


UPPER_FAMILIES = (
    "obs_upper", "obs_upper_gps", "obs_upper_light", "obs_upper_ard",
    "obs_upper_latest",
)


@pytest.mark.parametrize(
    "case", [item for family in UPPER_FAMILIES for item in case_parameters(family)]
)
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    kwargs.update(client=request.getfixturevalue("real_client"), strict=True)
    table = retrieve_obs_upper_air(**kwargs)

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataframe"
    assert isinstance(table, pd.DataFrame)
    if expected["nonempty"]:
        assert not table.empty
    columns = resolve_case_value(expected["columns"], dataset, request)
    assert set(columns).issubset(table.columns)
    if "count" in kwargs:
        assert len(table) <= kwargs["count"]
    if "station_matches" in expected:
        column = "Station_Id_C" if case["family"] == "obs_upper_gps" else "Station_Id_d"
        station_id = resolve_case_value(expected["station_matches"], dataset, request)
        assert table[column].astype(str).eq(str(station_id)).all()
    if "coordinates_within" in expected:
        region = resolve_case_value(expected["coordinates_within"], dataset, request)
        for column, start, end in (
            ("Lat", "start_latitude", "end_latitude"),
            ("Lon", "start_longitude", "end_longitude"),
        ):
            values = pd.to_numeric(table[column], errors="raise")
            lower, upper = sorted((region[start], region[end]))
            assert values.between(lower, upper).all()
    for key, column in (
        ("pressure_matches", "PRS_HWC"),
        ("height_matches", "GPH"),
        ("vertical_matches", "EVSS"),
    ):
        if key in expected:
            value = resolve_case_value(expected[key], dataset, request)
            assert pd.to_numeric(table[column], errors="raise").eq(value).all()
    if "flight_height_between" in expected:
        lower, upper = resolve_case_value(expected["flight_height_between"], dataset, request)
        assert pd.to_numeric(table["Flight_Heigh"], errors="raise").between(lower, upper).all()
