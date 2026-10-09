"""Offline point and station forecasts shared with the executable guide.

From the repository root: ``python -m examples.high_level.model_point``.
All tables are synthetic; no credentials or service connection are used.
"""

import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.model import retrieve_model_point
from nuwe_cmadaas.music import CMADaaSError


def make_model_point_client():
    """Register four query shapes, a multiple-point variant and empty/error tables."""
    transport = SyntheticTransport()
    base = {
        "dataCode": "SYNTHETIC_MODEL_POINT", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
    }
    columns = ["lat", "lon", "datetime", "level", "validtime", "synthetic_temperature_103"]
    station_columns = ["lat", "lon", "station_id_c", *columns[2:]]

    def point_row(lat, lon, lead, value):
        return [lat, lon, "20260102060000", "2", lead, value]

    def station_row(lead, value):
        return ["30.0", "110.0", "FAKE001", "20260102060000", "2", lead, value]

    def register(interface_id, selectors, rows, station=False):
        transport.register_api(
            "callAPI_to_array2D", interface_id, {**base, **selectors},
            make_array2d_content(rows=rows, element_names=station_columns if station else columns),
        )

    register(
        "getNafpEleAtPointByTimeAndLevelAndValidtime",
        {"validTime": "24", "latLons": "30.0/110.0"},
        [point_row("30.0", "110.0", "24", "280.0")],
    )
    register(
        "getNafpEleAtPointByTimeAndLevelAndValidtime",
        {"validTime": "24", "latLons": "30.0/110.0,31.0/111.0"},
        [point_row("30.0", "110.0", "24", "280.0"), point_row("31.0", "111.0", "24", "281.5")],
    )
    register(
        "getNafpEleAtPointByTimeAndLevelAndValidtimeRange",
        {"minVT": "6", "maxVT": "24", "latLons": "30.0/110.0"},
        [point_row("30.0", "110.0", lead, value)
         for lead, value in [("6", "276.0"), ("12", "278.0"), ("24", "280.0")]],
    )
    register(
        "getNafpEleByTimeAndLevelAndValidtimeAndStaID",
        {"validTime": "24", "staIds": "FAKE001"}, [station_row("24", "282.0")], station=True,
    )
    register(
        "getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID",
        {"minVT": "6", "maxVT": "24", "staIds": "FAKE001"},
        [station_row(lead, value) for lead, value in [("6", "278.0"), ("12", "280.0"), ("24", "282.0")]],
        station=True,
    )
    for code, error_code in [("SYNTHETIC_EMPTY", 0), ("SYNTHETIC_ERROR", -4234)]:
        transport.register_api(
            "callAPI_to_array2D", "getNafpEleAtPointByTimeAndLevelAndValidtime",
            {**base, "dataCode": code, "validTime": "24", "latLons": "30.0/110.0"},
            make_array2d_content(
                rows=[], element_names=columns, error_code=error_code,
                error_message="Synthetic model-point failure" if error_code else "",
            ),
        )
    return make_synthetic_music_client(transport), transport


def check_results(results, converted, transport, failed_code):
    """Check independent table values, fields, dtypes, attrs and explicit conversion."""
    point_columns = ["lat", "lon", "datetime", "level", "validtime", "synthetic_temperature_103"]
    station_columns = ["lat", "lon", "station_id_c", *point_columns[2:]]
    expected = {
        "point": ("getNafpEleAtPointByTimeAndLevelAndValidtime", False, False,
                  [["30.0", "110.0", "20260102060000", "2", "24", "280.0"]]),
        "multi_point": ("getNafpEleAtPointByTimeAndLevelAndValidtime", False, False,
                        [["30.0", "110.0", "20260102060000", "2", "24", "280.0"],
                         ["31.0", "111.0", "20260102060000", "2", "24", "281.5"]]),
        "point_range": ("getNafpEleAtPointByTimeAndLevelAndValidtimeRange", False, True,
                        [["30.0", "110.0", "20260102060000", "2", "6", "276.0"],
                         ["30.0", "110.0", "20260102060000", "2", "12", "278.0"],
                         ["30.0", "110.0", "20260102060000", "2", "24", "280.0"]]),
        "station": ("getNafpEleByTimeAndLevelAndValidtimeAndStaID", True, False,
                    [["30.0", "110.0", "FAKE001", "20260102060000", "2", "24", "282.0"]]),
        "station_range": ("getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID", True, True,
                          [["30.0", "110.0", "FAKE001", "20260102060000", "2", "6", "278.0"],
                           ["30.0", "110.0", "FAKE001", "20260102060000", "2", "12", "280.0"],
                           ["30.0", "110.0", "FAKE001", "20260102060000", "2", "24", "282.0"]]),
        "empty": ("getNafpEleAtPointByTimeAndLevelAndValidtime", False, False, []),
    }
    assert set(results) == set(expected)
    for name, (interface_id, station, lead_range, rows) in expected.items():
        table = results[name]
        assert isinstance(table, pd.DataFrame)
        assert table.columns.tolist() == (station_columns if station else point_columns)
        assert table.shape == (len(rows), len(table.columns))
        assert table.values.tolist() == rows
        assert all(isinstance(value, str) for value in table.to_numpy().ravel())
        if rows:
            assert all(pd.api.types.is_string_dtype(dtype) for dtype in table.dtypes)
        attrs = {
            "interface_id": interface_id, "time": "20260102060000",
            "level_type": "103", "level": "2",
            "request_time": "20260102000000", "response_time": "20260102000001",
        }
        if not lead_range:
            attrs["valid_time"] = "24"
        assert table.attrs == attrs
    assert converted["validtime"].tolist() == [6, 12, 24]
    assert converted["synthetic_temperature_103"].tolist() == [276.0, 278.0, 280.0]
    assert converted["valid_at"].tolist() == [
        pd.Timestamp("2026-01-02 12:00"), pd.Timestamp("2026-01-02 18:00"),
        pd.Timestamp("2026-01-03 06:00"),
    ]
    assert results["point_range"]["validtime"].tolist() == ["6", "12", "24"]
    assert failed_code == -4234
    assert len(transport.calls) == len(transport.responses) == 7
    assert all(response.closed for response in transport.responses)


def run_example():
    """Execute public queries, explicit conversions, and local error checks."""
    client, transport = make_model_point_client()
    common = {
        "data_code": "SYNTHETIC_MODEL_POINT", "parameter": "synthetic_temperature",
        "start_time": pd.Timestamp("2026-01-02 06:00"), "level_type": 103, "level": 2,
        "client": client, "strict": True,
    }
    results = {}
    for name, selectors in [
        ("point", {"point": (30.0, 110.0), "forecast_time": "24h"}),
        ("multi_point", {"point": [(30.0, 110.0), (31.0, 111.0)], "forecast_time": "24h"}),
        ("point_range", {"point": (30.0, 110.0), "forecast_time": ("6h", pd.Timedelta(hours=24))}),
        ("station", {"station": "FAKE001", "forecast_time": pd.Timedelta(hours=24)}),
        ("station_range", {"station": "FAKE001", "forecast_time": ("6h", "24h")}),
        ("empty", {"data_code": "SYNTHETIC_EMPTY", "point": (30.0, 110.0), "forecast_time": "24h"}),
    ]:
        results[name] = retrieve_model_point(**{**common, **selectors})
    converted = results["point_range"].copy()
    for column in ["lat", "lon", "level", "validtime", "synthetic_temperature_103"]:
        converted[column] = pd.to_numeric(converted[column], errors="raise")
    cycle = pd.to_datetime(converted["datetime"], format="%Y%m%d%H%M%S", errors="raise")
    converted["valid_at"] = cycle + pd.to_timedelta(converted["validtime"], unit="h")
    failed_code = None
    try:
        retrieve_model_point(
            **{**common, "data_code": "SYNTHETIC_ERROR"}, point=(30.0, 110.0), forecast_time="24h",
        )
    except CMADaaSError as error:
        failed_code = error.error_code
        assert error.interface_id == "getNafpEleAtPointByTimeAndLevelAndValidtime"
    else:
        raise AssertionError("service errors must raise in strict mode")
    default = {**common, "point": (30.0, 110.0), "forecast_time": "24h"}
    for selectors, error_type in [
        ({"station": "FAKE001"}, ValueError),
        ({"point": None}, UnsupportedQueryError),
        ({"point": (110.0, 30.0)}, ValueError),
        ({"point": []}, ValueError),
        ({"point": None, "station": ("FAKE001", "FAKE002")}, TypeError),
        ({"forecast_time": ("24h", "6h")}, ValueError),
        ({"forecast_time": ["6h", "24h"]}, TypeError),
        ({"forecast_time": "30min"}, ValueError),
        ({"level": None}, ValueError),
    ]:
        calls_before = len(transport.calls)
        try:
            retrieve_model_point(**{**default, **selectors})
        except error_type:
            assert len(transport.calls) == calls_before
        else:
            raise AssertionError(f"invalid selectors must fail before a request: {selectors}")
    check_results(results, converted, transport, failed_code)
    return results, converted


if __name__ == "__main__":
    results, converted = run_example()
    for name, table in results.items():
        print(f"\n{name}:\n{table.to_string(index=False)}")
        print(f"dtypes:\n{table.dtypes}")
        print(f"attrs: {table.attrs}")
    print(f"\nExplicitly converted lead range:\n{converted.to_string(index=False)}")
    print("\nAll synthetic model-point contracts passed.")
