"""Service-backed surface grid cases from the SURF_API catalog."""

import numpy as np
import pytest
import xarray as xr

from nuwe_cmadaas.obs import retrieve_obs_grid
from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("obs_grid"))
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    kwargs["client"] = request.getfixturevalue("real_client")
    kwargs["strict"] = True
    field = retrieve_obs_grid(**kwargs)

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataarray"
    assert isinstance(field, xr.DataArray)
    assert field.dims == ("latitude", "longitude")
    assert field.ndim == 2
    assert all(size > 0 for size in field.shape)
    assert field.shape == (
        field.sizes["latitude"], field.sizes["longitude"]
    )
    for axis in ("latitude", "longitude"):
        values = field.coords[axis].values
        assert values.ndim == 1
        assert len(values) == field.sizes[axis]
        assert np.isfinite(values).all()
        assert np.unique(values).size == values.size
    assert isinstance(field.name, str)
    assert "units" in field.attrs
    if dataset.get("expected_units"):
        assert field.attrs["units"] == dataset["expected_units"]

    if "region" in kwargs:
        region = kwargs["region"]
        for axis, start, end in (
            ("latitude", "start_latitude", "end_latitude"),
            ("longitude", "start_longitude", "end_longitude"),
        ):
            values = field.coords[axis].values
            lower, upper = sorted((region[start], region[end]))
            assert values.min() >= lower - 1e-4
            assert values.max() <= upper + 1e-4
