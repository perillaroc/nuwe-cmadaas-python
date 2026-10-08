"""Service-backed native Array2D response and DataFrame conversion."""

import numpy as np
import pandas as pd
import pytest

from nuwe_cmadaas.music import Array2D
from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("music_array2d"))
def test_registered_case(case, request, integration_profile, low_level_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    capability = low_level_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], capability, request)
    result = request.getfixturevalue("real_client").callAPI_to_array2D(**kwargs)

    assert isinstance(result, Array2D)
    assert result.ok, f"{case_id}: {result.request.error_code} {result.request.error_message}"
    assert result.request.error_code == 0
    assert result.request.row_count == result.row_count
    assert result.request.col_count == result.col_count
    assert result.data.shape == (result.row_count, result.col_count)
    expected = case["expected_return_contract"]
    assert expected["kind"] == "Array2D"
    assert result.element_names == expected["columns"]
    assert 0 < result.row_count <= expected["max_rows"]

    table = result.to_pandas()
    assert isinstance(table, pd.DataFrame)
    assert list(table.columns) == result.element_names
    assert table.shape == result.data.shape
    assert np.array_equal(table.to_numpy(), result.data)
    assert pd.to_datetime(table["datetime"], format="mixed").eq(pd.Timestamp(kwargs["params"]["time"])).all()
    assert pd.to_numeric(table["level"]).eq(int(kwargs["params"]["fcstLevel"])).all()
    assert pd.to_numeric(table["validtime"]).eq(int(kwargs["params"]["validTime"])).all()
    latitude, longitude = map(float, kwargs["params"]["latLons"].split("/"))
    assert np.isclose(pd.to_numeric(table["lat"]).to_numpy(), latitude).all()
    assert np.isclose(pd.to_numeric(table["lon"]).to_numpy(), longitude).all()
    lower, upper = capability["expected_value_bounds"]
    assert pd.to_numeric(table["TEM_103"]).between(lower, upper).all()
