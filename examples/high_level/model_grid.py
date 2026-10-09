"""Offline model-grid queries shared with the executable guide.

From the repository root: ``python -m examples.high_level.model_grid``.
All fields are synthetic; no credentials or service connection are used.
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
from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.music import CMADaaSError


def make_model_grid_client():
    """Register all eight query shapes and one synthetic service error."""
    transport = SyntheticTransport()
    base = {
        "dataCode": "SYNTHETIC_MODEL_GRID", "fcstEle": "synthetic_temperature",
        "time": "20260102060000",
    }
    layer = {"levelType": "100", "fcstLevel": "850"}
    rectangle = {"minLat": "30.0", "maxLat": "31.0", "minLon": "110.0", "maxLon": "111.0"}

    def register(interface_id, params, first_value, regional=False):
        if regional:
            content = make_grid_array2d_content(
                lons=[110.0, 111.0], end_lon=111.0,
                data=[first_value, first_value + 0.5, first_value + 1.5, first_value + 2],
            )
        else:
            content = make_grid_array2d_content(
                data=[first_value + offset for offset in [0, 0.5, 1, 1.5, 2, 2.5]],
            )
        transport.register_api("callAPI_to_gridArray2D", interface_id, params, content)

    register("getNafpEleGridByTimeAndLevelAndValidtime", {**base, **layer, "validTime": "24"}, 280)
    register(
        "getNafpEleGridInRectByTimeAndLevelAndValidtime",
        {**base, **layer, "validTime": "24", **rectangle}, 280, regional=True,
    )
    register(
        "getNafpEleGridByTimeAndLevelAndValidtimeAndFcstMember",
        {**base, **layer, "validTime": "24", "fcstMember": 0}, 290,
    )
    register(
        "getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember",
        {**base, **layer, "validTime": "24", "fcstMember": 10, **rectangle}, 300, regional=True,
    )
    register("getNafpAnaEleGridByTimeAndLevel", {**base, **layer}, 270)
    register("getNafpAnaEleGridInRectByTimeAndLevel", {**base, **layer, **rectangle}, 265, regional=True)
    register("getNafpEleGridByTime", base, 260)
    register("getNafpEleGridInRectByTime", {**base, **rectangle}, 255, regional=True)
    transport.register_api(
        "callAPI_to_gridArray2D", "getNafpEleGridByTimeAndLevelAndValidtime",
        {**base, **layer, "validTime": "24", "dataCode": "SYNTHETIC_ERROR"},
        make_grid_array2d_content(error_code=-3234, error_message="Synthetic model-grid failure"),
    )
    return make_synthetic_music_client(transport), transport


def check_results(results, transport, failed_code):
    """Check coordinates, independent values, units and exact query metadata."""
    expected = {
        "forecast": ("getNafpEleGridByTimeAndLevelAndValidtime", 280, False, True, None),
        "regional": ("getNafpEleGridInRectByTimeAndLevelAndValidtime", 280, True, True, None),
        "control": ("getNafpEleGridByTimeAndLevelAndValidtimeAndFcstMember", 290, False, True, 0),
        "member": ("getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember", 300, True, True, 10),
        "analysis": ("getNafpAnaEleGridByTimeAndLevel", 270, False, False, None),
        "analysis_region": ("getNafpAnaEleGridInRectByTimeAndLevel", 265, True, False, None),
        "time_only": ("getNafpEleGridByTime", 260, False, False, None),
        "time_only_region": ("getNafpEleGridInRectByTime", 255, True, False, None),
    }
    assert set(results) == set(expected)
    for name, (interface_id, first, regional, forecast, member) in expected.items():
        field = results[name]
        lons = [110.0, 111.0] if regional else [110.0, 111.0, 112.0]
        values = [[first, first + 0.5], [first + 1.5, first + 2]] if regional else [
            [first, first + 0.5, first + 1], [first + 1.5, first + 2, first + 2.5],
        ]
        assert isinstance(field, xr.DataArray)
        assert field.dims == ("latitude", "longitude")
        assert field.shape == (2, len(lons))
        assert set(field.coords) == {"latitude", "longitude"}
        assert field.latitude.values.tolist() == [30.0, 31.0]
        assert field.longitude.values.tolist() == lons
        assert field.latitude.attrs["units"] == "degrees_north"
        assert field.longitude.attrs["units"] == "degrees_east"
        assert np.issubdtype(field.dtype, np.floating)
        np.testing.assert_allclose(field.values, values)
        assert field.name == "synthetic_temperature"
        attrs = {
            "units": "K", "interface_id": interface_id, "time": "20260102060000",
            "request_time": "20260102000000", "response_time": "20260102000001",
        }
        if not name.startswith("time_only"):
            attrs.update(level_type="100", level="850")
        if forecast:
            attrs["valid_time"] = "24"
        if member is not None:
            attrs["member"] = member
        assert field.attrs == attrs
    assert results["forecast"].sel(latitude=30.0, longitude=111.0).item() == 280.5
    assert failed_code == -3234
    assert len(transport.calls) == len(transport.responses) == 9
    assert all(response.closed for response in transport.responses)


def run_example():
    """Execute each public query and check local errors before any request."""
    client, transport = make_model_grid_client()
    common = {
        "data_code": "SYNTHETIC_MODEL_GRID", "parameter": "synthetic_temperature",
        "start_time": pd.Timestamp("2026-01-02 06:00"), "client": client, "strict": True,
    }
    layer = {"level_type": 100, "level": 850}
    rectangle = {
        "type": "rect", "start_longitude": 111, "end_longitude": 110,
        "start_latitude": 31, "end_latitude": 30,
    }
    results = {}
    for name, selectors in [
        ("forecast", {**layer, "forecast_time": "24h"}),
        ("regional", {**layer, "forecast_time": pd.Timedelta(hours=24), "region": rectangle}),
        ("control", {**layer, "forecast_time": "24h", "number": 0}),
        ("member", {**layer, "forecast_time": "24h", "number": 10, "region": rectangle}),
        ("analysis", {**layer, "data_type": "analysis"}),
        ("analysis_region", {**layer, "data_type": "analysis", "region": rectangle}),
        ("time_only", {}),
        ("time_only_region", {"region": rectangle}),
    ]:
        results[name] = retrieve_model_grid(**common, **selectors)
    failed_code = None
    try:
        retrieve_model_grid(
            **{**common, "data_code": "SYNTHETIC_ERROR"}, **layer, forecast_time="24h",
        )
    except CMADaaSError as error:
        failed_code = error.error_code
        assert error.interface_id == "getNafpEleGridByTimeAndLevelAndValidtime"
    else:
        raise AssertionError("service errors must raise in strict mode")
    for selectors, error_type in [
        ({"start_time": None}, UnsupportedQueryError),
        ({"level_type": 100}, ValueError),
        ({**layer, "data_type": "analysis", "forecast_time": "0h"}, UnsupportedQueryError),
        ({"forecast_time": "24h"}, UnsupportedQueryError),
        ({**layer, "forecast_time": ("0h", "24h")}, TypeError),
        ({**layer, "forecast_time": "30min"}, ValueError),
        ({"data_type": "bogus"}, ValueError),
        ({"region": {"type": "region", "admin_codes": "110000"}}, UnsupportedQueryError),
    ]:
        calls_before = len(transport.calls)
        try:
            retrieve_model_grid(**{**common, **selectors})
        except error_type:
            assert len(transport.calls) == calls_before
        else:
            raise AssertionError(f"invalid selectors must fail before a request: {selectors}")
    check_results(results, transport, failed_code)
    return results


if __name__ == "__main__":
    for name, field in run_example().items():
        print(f"\n{name}:\n{field}")
        print(f"values:\n{field.values}")
        print(f"attrs: {field.attrs}")
    print("\nAll synthetic model-grid contracts passed.")
