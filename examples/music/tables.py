"""Offline native Array2D workflow shared with the executable table guide.

From the repository root: ``python -m examples.music.tables``.
All responses are synthetic protobuf messages; no service credentials are used.
"""

import numpy as np
import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.music import CMADaaSDecodeError, CMADaaSRequestError
from nuwe_cmadaas.music.data import Array2D


def make_table_client():
    """Register exact native queries for success, empty, service and decode errors."""
    transport = SyntheticTransport()
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    params = {
        "dataCode": "SYNTHETIC_TABLE", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "latLons": "30.0/110.0,31.0/111.0",
    }
    columns = ["lat", "lon", "datetime", "level", "validtime", "synthetic_temperature_103"]
    rows = [
        ["30.0", "110.0", "20260102060000", "2", "24", "280.0"],
        ["31.0", "111.0", "20260102060000", "2", "24", "281.5"],
    ]
    for code, content in [
        ("SYNTHETIC_TABLE", make_array2d_content(rows=rows, element_names=columns)),
        ("SYNTHETIC_EMPTY", make_array2d_content(rows=[], element_names=columns)),
        ("SYNTHETIC_ERROR", make_array2d_content(
            rows=[], element_names=columns, error_code=-6234,
            error_message="Synthetic table service failure",
        )),
        ("SYNTHETIC_MALFORMED", make_array2d_content(
            rows=rows, element_names=columns, row_count=3,
        )),
    ]:
        transport.register_api(
            "callAPI_to_array2D", interface_id, {**params, "dataCode": code}, content,
        )
    return make_synthetic_music_client(transport), transport


def check_results(responses, table, converted, transport, params):
    """Check raw protobuf decoding, request state, conversion and closed responses."""
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    columns = ["lat", "lon", "datetime", "level", "validtime", "synthetic_temperature_103"]
    rows = [
        ["30.0", "110.0", "20260102060000", "2", "24", "280.0"],
        ["31.0", "111.0", "20260102060000", "2", "24", "281.5"],
    ]
    assert params == {
        "dataCode": "SYNTHETIC_TABLE", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "latLons": "30.0/110.0,31.0/111.0",
    }
    assert set(responses) == {"success", "empty", "failed", "malformed"}
    success = responses["success"]
    assert isinstance(success, Array2D)
    assert success.ok and success.request.error_code == 0
    assert success.request.error_message == "" and success.request.cause is None
    assert (success.row_count, success.col_count) == (2, 6)
    assert (success.request.row_count, success.request.col_count) == (2, 6)
    assert success.element_names == columns
    assert success.data.shape == (2, 6) and success.data.dtype.kind == "U"
    assert success.data.tolist() == rows
    assert success.request.request_elements == "synthetic_elements"
    assert success.request.request_params == "synthetic_params"
    assert success.request.take_time == 0
    assert success.raise_for_error(interface_id=interface_id, params=params) is success
    assert isinstance(table, pd.DataFrame) and table.shape == (2, 6)
    assert table.columns.tolist() == columns
    assert np.array_equal(table.to_numpy(), success.data)
    assert all(isinstance(value, str) for value in table.to_numpy().ravel())
    assert all(pd.api.types.is_string_dtype(dtype) for dtype in table.dtypes)
    metadata = {
        "interface_id": interface_id, "time": "20260102060000", "level_type": "103",
        "level": "2", "valid_time": "24",
    }
    attrs = {**metadata, "request_time": "20260102000000", "response_time": "20260102000001"}
    assert success.metadata == metadata and table.attrs == attrs
    assert converted["synthetic_temperature_103"].tolist() == [280.0, 281.5]
    assert pd.api.types.is_numeric_dtype(converted["synthetic_temperature_103"])
    assert table["synthetic_temperature_103"].tolist() == ["280.0", "281.5"]
    empty = responses["empty"]
    assert isinstance(empty, Array2D) and empty.ok
    assert empty.raise_for_error() is empty
    assert empty.element_names == columns and empty.data.shape == (0, 6)
    assert (empty.row_count, empty.col_count) == (0, 6)
    assert (empty.request.row_count, empty.request.col_count) == (0, 6)
    empty_table = empty.to_pandas()
    assert empty_table.empty and empty_table.shape == (0, 6)
    assert empty_table.columns.tolist() == columns and empty_table.attrs == attrs
    assert responses["failed"].data.shape == (0, 0)
    assert responses["failed"].element_names == columns
    assert (responses["failed"].row_count, responses["failed"].col_count) == (0, 0)
    for name, code, error_type in [
        ("failed", -6234, CMADaaSRequestError),
        ("malformed", -10003, CMADaaSDecodeError),
    ]:
        response = responses[name]
        assert isinstance(response, Array2D) and not response.ok
        assert response.request.error_code == code
        error_params = {**params, "dataCode": "SYNTHETIC_ERROR" if name == "failed"
                        else "SYNTHETIC_MALFORMED"}
        try:
            response.raise_for_error(interface_id=interface_id, params=error_params)
        except error_type as error:
            assert error.error_code == code and error.interface_id == interface_id
            assert error.params == error_params
            if name == "malformed":
                assert isinstance(error.cause, ValueError) and error.__cause__ is error.cause
            else:
                assert error.cause is None
        else:
            raise AssertionError("failed responses must raise with explicit context")
        try:
            response.to_pandas()
        except error_type as error:
            assert error.error_code == code and error.interface_id is None
        else:
            raise AssertionError("failed responses must not convert to empty tables")
    assert len(transport.calls) == len(transport.responses) == 4
    assert all(response.closed and not response.streamed for response in transport.responses)


def run_example():
    """Call the native API, inspect status and explicitly convert string values."""
    client, transport = make_table_client()
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    params = {
        "dataCode": "SYNTHETIC_TABLE", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "latLons": "30.0/110.0,31.0/111.0",
    }
    success = client.callAPI_to_array2D(interface_id, params)
    success.raise_for_error(interface_id=interface_id, params=params)
    table = success.to_pandas()
    converted = table.copy()
    converted["synthetic_temperature_103"] = pd.to_numeric(
        converted["synthetic_temperature_103"], errors="raise",
    )
    responses = {"success": success}
    for name, code in [("empty", "SYNTHETIC_EMPTY"), ("failed", "SYNTHETIC_ERROR"),
                       ("malformed", "SYNTHETIC_MALFORMED")]:
        responses[name] = client.callAPI_to_array2D(interface_id, {**params, "dataCode": code})
    check_results(responses, table, converted, transport, params)
    return responses, table, converted


if __name__ == "__main__":
    responses, table, converted = run_example()
    for name, response in responses.items():
        print(f"{name}: ok={response.ok}, code={response.request.error_code}, "
              f"shape={response.data.shape}")
    print(f"\nColumns: {responses['success'].element_names}")
    print(f"Raw strings:\n{responses['success'].data}")
    print(f"\nDataFrame:\n{table.to_string(index=False)}")
    print(f"dtypes:\n{table.dtypes}\nattrs: {table.attrs}")
    print(f"\nExplicit numeric conversion:\n{converted.to_string(index=False)}")
    print("\nAll synthetic native table contracts passed.")
