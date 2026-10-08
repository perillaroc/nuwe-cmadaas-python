"""Service-backed native grid responses and xarray conversions."""

import numpy as np
import pytest
import xarray as xr

from nuwe_cmadaas.music import GridArray2D, GridScalar2D, GridVector2D
from tests.integration.case_registry import case_parameters, resolve_case_value


GRID_METHODS = {
    "music_grid_array2d": ("callAPI_to_gridArray2D", GridArray2D),
    "music_grid_scalar2d": ("callAPI_to_gridScalar2D", GridScalar2D),
    "music_grid_vector2d": ("callAPI_to_gridVector2D", GridVector2D),
}


@pytest.mark.parametrize(
    "case",
    case_parameters("music_grid_array2d")
    + case_parameters("music_grid_scalar2d")
    + case_parameters("music_grid_vector2d"),
)
def test_registered_case(case, request, integration_profile, low_level_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    capability = low_level_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], capability, request)
    method_name, response_type = GRID_METHODS[case["family"]]
    result = getattr(request.getfixturevalue("real_client"), method_name)(**kwargs)

    assert isinstance(result, response_type)
    assert result.ok, f"{case_id}: {result.request.error_code} {result.request.error_message}"
    assert result.request.error_code == 0
    assert result.lat_count > 0 and result.lon_count > 0
    expected = case["expected_return_contract"]
    assert expected["kind"] == response_type.__name__
    assert result.lat_count * result.lon_count <= expected["max_cells"]
    assert len(result.lats) == result.lat_count
    assert len(result.lons) == result.lon_count

    field = result.to_xarray()
    assert tuple(field.sizes) == tuple(expected["dims"])
    assert field.sizes["latitude"] == result.lat_count
    assert field.sizes["longitude"] == result.lon_count
    for axis, bounds in (("latitude", (result.start_lat, result.end_lat)),
                         ("longitude", (result.start_lon, result.end_lon))):
        values = field.coords[axis].values
        assert np.isfinite(values).all()
        assert np.unique(values).size == values.size
        assert np.allclose(values, result.lats if axis == "latitude" else result.lons)
        if case["family"] != "music_grid_vector2d":
            lower, upper = sorted(bounds)
            assert values.min() >= lower - 1e-4
            assert values.max() <= upper + 1e-4

    if isinstance(field, xr.DataArray):
        assert field.shape == (result.lat_count, result.lon_count)
        finite = field.values[np.isfinite(field.values)]
        assert finite.size > 0
        lower, upper = capability["expected_value_bounds"]
        assert np.all((finite >= lower) & (finite <= upper))
        assert np.allclose(field.values, result.data, equal_nan=True)
        assert "units" in field.attrs
    else:
        assert isinstance(field, xr.Dataset)
        assert set(field.data_vars) == set(expected["components"])
        for component in field.data_vars.values():
            assert component.shape == (result.lat_count, result.lon_count)
            finite = component.values[np.isfinite(component.values)]
            assert finite.size > 0
            assert np.any(np.abs(finite) > 1e-6)
        assert np.allclose(field[result.u_element_name].values, result.u_datas, equal_nan=True)
        assert np.allclose(field[result.v_element_name].values, result.v_datas, equal_nan=True)

    if "minLat" in kwargs["params"]:
        # CMADaaS snaps the requested rectangle to grid-cell centers; an edge
        # center can lie up to half a grid interval outside the request.
        for axis, minimum, maximum, step in (
            ("latitude", "minLat", "maxLat", result.lat_step),
            ("longitude", "minLon", "maxLon", result.lon_step),
        ):
            values = field.coords[axis].values
            tolerance = abs(step) / 2 + 1e-3
            assert values.min() >= float(kwargs["params"][minimum]) - tolerance
            assert values.max() <= float(kwargs["params"][maximum]) + tolerance
