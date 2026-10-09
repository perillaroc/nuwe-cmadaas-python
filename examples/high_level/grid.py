"""Offline surface-grid queries shared with the executable grid guide.

From the repository root: ``python -m examples.high_level.grid``.
All responses are synthetic; no credentials or service connection are used.
"""

import numpy as np
import pandas as pd
import xarray as xr

from examples._support import (
    SyntheticTransport,
    make_grid_array2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.obs import retrieve_obs_grid


def make_grid_client():
    """Register exact requests for a full field and a small rectangle."""
    transport = SyntheticTransport()
    params = {
        "dataCode": "SYNTHETIC_GRID",
        "fcstEle": "synthetic_temperature",
        "time": "20260102000000",
    }
    transport.register_api(
        "callAPI_to_gridArray2D", "getSurfEleGridByTime", params,
        make_grid_array2d_content(),
    )
    transport.register_api(
        "callAPI_to_gridArray2D", "getSurfEleGridInRectByTime",
        {
            **params, "minLat": "30.0", "maxLat": "31.0",
            "minLon": "110.0", "maxLon": "111.0",
        },
        make_grid_array2d_content(
            lons=[110.0, 111.0], end_lon=111.0,
            data=[280.0, 280.5, 281.5, 282.0],
        ),
    )
    return make_synthetic_music_client(transport), transport


def check_results(field, regional, transport):
    """Check independent coordinate, value, unit and metadata expectations."""
    for result, interface_id, lons, values in [
        (
            field, "getSurfEleGridByTime", [110.0, 111.0, 112.0],
            [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]],
        ),
        (
            regional, "getSurfEleGridInRectByTime", [110.0, 111.0],
            [[280.0, 280.5], [281.5, 282.0]],
        ),
    ]:
        assert isinstance(result, xr.DataArray)
        assert result.dims == ("latitude", "longitude")
        assert result.shape == (2, len(lons))
        assert set(result.coords) == {"latitude", "longitude"}
        assert result.latitude.values.tolist() == [30.0, 31.0]
        assert result.longitude.values.tolist() == lons
        assert result.latitude.attrs["units"] == "degrees_north"
        assert result.longitude.attrs["units"] == "degrees_east"
        assert np.issubdtype(result.dtype, np.floating)
        np.testing.assert_allclose(result.values, values)
        assert result.name == "synthetic_temperature"
        assert result.attrs == {
            "units": "K", "interface_id": interface_id,
            "time": "20260102000000",
            "request_time": "20260102000000",
            "response_time": "20260102000001",
        }
    assert field.sel(latitude=30.0, longitude=111.0).item() == 280.5
    assert len(transport.calls) == 2
    assert len(transport.responses) == 2
    assert all(response.closed for response in transport.responses)


def run_example():
    """Execute the public calls and reject unsupported selectors locally."""
    client, transport = make_grid_client()
    common = {
        "data_code": "SYNTHETIC_GRID",
        "parameter": "synthetic_temperature",
        "client": client,
        "strict": True,
    }
    time = pd.Timestamp("2026-01-02")
    field = retrieve_obs_grid(**common, time=time)
    regional = retrieve_obs_grid(
        **common, time=time,
        region={
            "type": "rect", "start_longitude": 111, "end_longitude": 110,
            "start_latitude": 31, "end_latitude": 30,
        },
    )
    for selectors, error_type in [
        ({}, UnsupportedQueryError),
        (
            {"time": pd.Interval(time, time + pd.Timedelta(hours=6), closed="left")},
            UnsupportedQueryError,
        ),
        (
            {"time": time, "region": {"type": "region", "admin_codes": "110000"}},
            UnsupportedQueryError,
        ),
        ({"time": pd.Timedelta(hours=6)}, TypeError),
    ]:
        calls_before = len(transport.calls)
        try:
            retrieve_obs_grid(**common, **selectors)
        except error_type:
            assert len(transport.calls) == calls_before
        else:
            raise AssertionError(f"unsupported selectors must fail locally: {selectors}")
    check_results(field, regional, transport)
    return field, regional


if __name__ == "__main__":
    for name, result in zip(("full field", "rectangle"), run_example()):
        print(f"\n{name}:\n{result}")
        print(f"values:\n{result.values}")
        print(f"attrs: {result.attrs}")
    print("\nAll synthetic grid contracts passed.")
