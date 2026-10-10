"""Service-backed forecast and analysis grids from the NAFP_API catalog."""

import numpy as np
import pytest
import xarray as xr

from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.music import CMADaaSRequestError
from nuwe_cmadaas.util import forecast_hours
from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize(
    "case", case_parameters("model_grid_forecast") + case_parameters("model_grid_analysis")
)
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    field = retrieve_model_grid(
        **kwargs, client=request.getfixturevalue("real_client"), strict=True
    )

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataarray"
    assert isinstance(field, xr.DataArray)
    assert field.dims == tuple(expected["dims"])
    assert field.ndim == 2
    assert all(size > 0 for size in field.shape)
    assert field.shape == (field.sizes["latitude"], field.sizes["longitude"])
    assert np.isfinite(field.values).any()
    for axis in field.dims:
        values = field.coords[axis].values
        assert values.ndim == 1
        assert values.size == field.sizes[axis]
        assert np.isfinite(values).all()
        assert np.unique(values).size == values.size
    optional_metadata = expected.get("response_metadata_optional", False)
    assert isinstance(field.name, str)
    if not optional_metadata:
        assert field.name
    assert isinstance(field.attrs.get("units"), str)
    if dataset.get("expected_units") and (field.attrs["units"] or not optional_metadata):
        assert field.attrs["units"] == dataset["expected_units"]

    assert field.attrs["interface_id"] == case["interface_id"]
    assert field.attrs["time"] == kwargs["start_time"].strftime("%Y%m%d%H%M%S")
    if "level" in kwargs:
        assert field.attrs["level_type"] == str(kwargs["level_type"])
        assert field.attrs["level"] == str(kwargs["level"])
    else:
        assert "level" not in field.attrs
    if "forecast_time" in kwargs:
        assert field.attrs["valid_time"] == str(forecast_hours(kwargs["forecast_time"]))
    else:
        assert "valid_time" not in field.attrs
    if "number" in kwargs:
        assert field.attrs["member"] == kwargs["number"]
    else:
        assert "member" not in field.attrs

    if "region" in kwargs:
        region = kwargs["region"]
        for axis, start, end in (
            ("latitude", "start_latitude", "end_latitude"),
            ("longitude", "start_longitude", "end_longitude"),
        ):
            values = field.coords[axis].values
            lower, upper = sorted((region[start], region[end]))
            step = np.max(np.abs(np.diff(values))) if values.size > 1 else 0.0
            assert ((values >= lower - 1e-4) & (values <= upper + 1e-4)).any()
            assert values.min() >= lower - step - 1e-4
            assert values.max() <= upper + step + 1e-4


REPS_CONTROL_CODE = "NAFP_GRAPESREPS_FOR_FTM_CHN"
REPS_MEMBER_CODE = "NAFP_GRAPESREPS_FOR_FTM_DIS_CHN"


@pytest.mark.parametrize(
    ("data_code", "extra_kwargs", "expected_code"),
    [
        (REPS_CONTROL_CODE, {"future_time": True}, -1),
        (REPS_CONTROL_CODE, {"forecast_time": "888h"}, -9002),
        (REPS_MEMBER_CODE, {"number": 99}, -9002),
        (REPS_MEMBER_CODE, {"parameter": "NON_EXIST", "number": 99}, -3001),
        (REPS_MEMBER_CODE, {"level_type": 103, "level": 100, "number": 99}, -9002),
        (REPS_MEMBER_CODE, {"level": 851, "number": 99}, -9002),
    ],
)
def test_reps_service_error_codes(data_code, extra_kwargs, expected_code, start_time_for_reps, future_start_date):
    """Preserve the legacy negative scenarios without matching server prose."""
    future = extra_kwargs.get("future_time", False)
    kwargs = {
        "data_code": data_code,
        "parameter": "TEM",
        "start_time": future_start_date if future else start_time_for_reps,
        "forecast_time": "24h",
        "level_type": 100,
        "level": 850,
        "number": 0 if data_code == REPS_CONTROL_CODE else 10,
        "strict": True,
    }
    kwargs.update({key: value for key, value in extra_kwargs.items() if key != "future_time"})

    with pytest.raises(CMADaaSRequestError) as raised:
        retrieve_model_grid(**kwargs)

    assert raised.value.error_code == expected_code
