"""Shared synthetic queries and independent checks for result/error guides.

The guides show the public calls; all temperatures, markers and failures here
are fictional. No real service capability or missing-value policy is implied.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from examples._support import (
    SyntheticTransport, make_array2d_content, make_files_info_content,
    make_grid_array2d_content, make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.music import CMADaaSError, CMADaaSQueryError, MusicError


def make_results_client():
    """Register strings, a grid with a sentinel, and genuine empty responses."""
    transport = SyntheticTransport()
    columns = ["Station_Id_C", "Lat", "Lon", "TEM"]
    common = {"elements": ",".join(columns), "times": "20260102000000", "orderby": "Station_ID_d:asc"}
    for code, rows in [
        ("SYNTHETIC_RESULTS", [
            ("FAKE001", "30.0", "110.0", "280.0"),
            ("FAKE002", "31.0", "111.0", "999999"),
            ("FAKE003", "30.5", "110.5", "bad"),
            ("FAKE004", "31.5", "111.5", "281.5"),
        ]),
        ("SYNTHETIC_EMPTY", []),
    ]:
        transport.register_api("callAPI_to_array2D", "getSurfEleByTime", {**common, "dataCode": code},
                               make_array2d_content(element_names=columns, rows=rows))
    for code, content in [
        ("SYNTHETIC_RESULTS", make_grid_array2d_content(data=[280.0, 999999.0, 281.0, 281.5, 282.0, 282.5])),
        ("SYNTHETIC_EMPTY", make_grid_array2d_content(data=[], lats=[], lons=[], lat_count=0, lon_count=0)),
    ]:
        transport.register_api("callAPI_to_gridArray2D", "getSurfEleGridByTime",
                               {"dataCode": code, "fcstEle": "synthetic_temperature", "time": "20260102000000"},
                               content)
    url = "https://synthetic.invalid/handling/result.bin"
    transport.register_download(url, b"FAKE")
    for code, infos in [
        ("SYNTHETIC_RESULTS", [{"file_name": "result.bin", "size": "4", "file_url": url}]),
        ("SYNTHETIC_EMPTY", []),
    ]:
        transport.register_api("callAPI_to_fileList", "getSurfFileByTime",
                               {"dataCode": code, "times": "20260102000000", "limitCnt": 1},
                               make_files_info_content(file_infos=infos))
    return make_synthetic_music_client(transport), transport


def check_results(table, cleaned, invalid, field, celsius, empty_table, empty_field, paths, empty_paths,
                  output_root, transport):
    """Check independent expected values, metadata, disk contents and cleanup state."""
    assert isinstance(table, pd.DataFrame) and table.shape == (4, 4)
    assert table.columns.tolist() == ["Station_Id_C", "Lat", "Lon", "TEM"]
    assert table["TEM"].tolist() == ["280.0", "999999", "bad", "281.5"]
    assert all(isinstance(value, str) for value in table.values.flat)
    assert table.attrs == {"interface_id": "getSurfEleByTime", "request_time": "20260102000000",
                           "response_time": "20260102000001"}
    assert invalid.tolist() == [False, False, True, False]
    np.testing.assert_allclose(cleaned["TEM_C"].to_numpy(dtype=float), [6.85, np.nan, np.nan, 8.35], equal_nan=True)
    assert cleaned["Station_Id_C"].tolist() == ["FAKE001", "FAKE002", "FAKE003", "FAKE004"]
    assert cleaned.attrs == {**table.attrs, "TEM_C_units": "degC", "missing_policy": "synthetic 999999; invalid tokens audited"}
    assert isinstance(field, xr.DataArray) and field.shape == (2, 3)
    assert field.dims == celsius.dims == ("latitude", "longitude")
    assert field.name == "synthetic_temperature" and field.dtype == np.dtype("float32")
    np.testing.assert_array_equal(field.values, [[280.0, 999999.0, 281.0], [281.5, 282.0, 282.5]])
    np.testing.assert_allclose(celsius.values, [[6.85, np.nan, 7.85], [8.35, 8.85, 9.35]], atol=2e-5, equal_nan=True)
    assert celsius.name == "synthetic_temperature_celsius"
    assert celsius.attrs == {**field.attrs, "units": "degC", "missing_policy": "synthetic 999999"}
    assert field.attrs == {"units": "K", "interface_id": "getSurfEleGridByTime", "time": "20260102000000",
                           "request_time": "20260102000000", "response_time": "20260102000001"}
    for result in [field, celsius]:
        assert set(result.coords) == {"latitude", "longitude"}
        assert result.latitude.values.tolist() == [30.0, 31.0]
        assert result.longitude.values.tolist() == [110.0, 111.0, 112.0]
        assert result.latitude.attrs["units"] == "degrees_north"
        assert result.longitude.attrs["units"] == "degrees_east"
    assert isinstance(empty_table, pd.DataFrame) and empty_table.shape == (0, 4)
    assert empty_table.columns.tolist() == table.columns.tolist()
    assert isinstance(empty_field, xr.DataArray) and empty_field.shape == (0, 0) and empty_field.size == 0
    assert paths == [Path(output_root) / "files" / "result.bin"]
    assert paths[0].is_file() and paths[0].stat().st_size == 4 and paths[0].read_bytes() == b"FAKE"
    assert empty_paths == [] and not (Path(output_root) / "empty").exists()
    assert [path.relative_to(output_root).as_posix() for path in Path(output_root).rglob("*") if path.is_file()] == ["files/result.bin"]
    assert not list(Path(output_root).rglob("*.part"))
    assert len(transport.calls) == len(transport.responses) == 7
    assert sum(response.streamed for response in transport.responses) == 1
    assert all(response.closed for response in transport.responses)


def make_errors_client():
    """Register business/authentication/decode failures and an empty success."""
    transport = SyntheticTransport()
    common = {"elements": "Station_Id_C,TEM", "times": "20260102000000", "orderby": "Station_ID_d:asc"}
    for code, content in [
        ("SYNTHETIC_FAILURE", make_array2d_content(error_code=-11234, error_message="Synthetic query failure")),
        ("SYNTHETIC_AUTH", make_array2d_content(error_code=-1004, error_message="Synthetic authentication failure")),
        ("SYNTHETIC_DECODE", b"\xff"),
        ("SYNTHETIC_EMPTY", make_array2d_content(element_names=["Station_Id_C", "TEM"], rows=[])),
    ]:
        transport.register_api("callAPI_to_array2D", "getSurfEleByTime", {**common, "dataCode": code}, content)
    return make_synthetic_music_client(transport), transport


def check_errors(legacy, notices, caught, raw, empty, local_errors, output_root, transport):
    """Check compatibility, exception identity/context, local guards and no disk output."""
    assert isinstance(legacy, MusicError) and legacy.code == -11234
    assert legacy.message == "Synthetic query failure" and not isinstance(legacy, BaseException)
    assert bool(legacy) is True  # An error result has no special false truth value.
    assert len(notices) == 1 and "MusicError" in notices[0]
    for name, error_type, code in [
        ("strict", "CMADaaSRequestError", -11234), ("raw", "CMADaaSRequestError", -11234),
        ("conversion", "CMADaaSRequestError", -11234),
        ("auth", "CMADaaSAuthenticationError", -1004), ("decode", "CMADaaSDecodeError", -10003),
    ]:
        error = caught[name]
        assert isinstance(error, CMADaaSError) and type(error).__name__ == error_type and error.error_code == code
        if name == "conversion":
            assert error.interface_id is None and error.params is None
        else:
            assert error.interface_id == "getSurfEleByTime"
    assert caught["strict"].params == {"dataCode": "SYNTHETIC_FAILURE", "elements": "Station_Id_C,TEM",
                                      "times": "20260102000000", "orderby": "Station_ID_d:asc"}
    assert caught["raw"].params["token"] == "<redacted>"
    assert caught["raw"].request_id is None and caught["raw"].retries == 0
    assert not raw.ok and raw.request.error_code == -11234
    assert isinstance(empty, pd.DataFrame) and empty.shape == (0, 2)
    assert local_errors == {"count": "ValueError", "time": "TypeError", "latest_filter": "UnsupportedQueryError",
                            "config_default": "FileNotFoundError", "config_strict": "FileNotFoundError"}
    assert issubclass(UnsupportedQueryError, CMADaaSQueryError)
    assert list(Path(output_root).iterdir()) == []
    assert len(transport.calls) == len(transport.responses) == 6
    assert all(response.closed and not response.streamed for response in transport.responses)
