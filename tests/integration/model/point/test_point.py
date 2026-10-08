"""Service-backed forecast interpolation at coordinates and station IDs."""

import pandas as pd
import pytest

from nuwe_cmadaas.model import retrieve_model_point
from nuwe_cmadaas.util import forecast_hour_range, forecast_hours
from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("model_point"))
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    table = retrieve_model_point(
        **kwargs, client=request.getfixturevalue("real_client"), strict=True
    )

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataframe"
    assert isinstance(table, pd.DataFrame)
    assert not table.empty
    assert len(table) <= dataset["max_rows"]
    assert set(resolve_case_value(expected["columns"], dataset, request)) <= set(table.columns)

    dates = pd.to_datetime(table["datetime"].astype(str), format="mixed", errors="raise")
    assert dates.eq(kwargs["start_time"]).all()
    levels = pd.to_numeric(table["level"], errors="raise")
    assert levels.eq(kwargs["level"]).all()

    valid_times = pd.to_numeric(table["validtime"], errors="raise")
    if isinstance(kwargs["forecast_time"], tuple):
        lower, upper = forecast_hour_range(kwargs["forecast_time"])
        assert valid_times.between(lower, upper).all()
        assert valid_times.nunique() > 1
    else:
        assert valid_times.eq(forecast_hours(kwargs["forecast_time"])).all()

    latitudes = pd.to_numeric(table["lat"], errors="raise")
    longitudes = pd.to_numeric(table["lon"], errors="raise")
    assert latitudes.between(-90, 90).all()
    assert longitudes.between(-180, 180).all()
    if "point_matches" in expected:
        latitude, longitude = resolve_case_value(expected["point_matches"], dataset, request)
        assert (latitudes - latitude).abs().le(1e-4).all()
        assert (longitudes - longitude).abs().le(1e-4).all()
    if "points_match" in expected:
        points = resolve_case_value(expected["points_match"], dataset, request)
        actual = set(zip(latitudes.round(4), longitudes.round(4)))
        wanted = {(round(lat, 4), round(lon, 4)) for lat, lon in points}
        assert actual == wanted
        assert len(table) == len(points)
    if "station_matches" in expected:
        station_id = resolve_case_value(expected["station_matches"], dataset, request)
        assert table["station_id_c"].astype(str).eq(station_id).all()

    temperature = pd.to_numeric(table["TEM_103"], errors="raise")
    lower, upper = dataset["expected_value_bounds"]
    assert temperature.between(lower, upper).all()
