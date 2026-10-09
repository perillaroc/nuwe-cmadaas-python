"""Offline surface-station queries shared with the executable station guide.

From the repository root: ``python -m examples.high_level.station``.
All responses are synthetic; no credentials or service connection are used.
"""

import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.obs import retrieve_obs_station


def make_station_client():
    """Register exact requests and small, deliberately different schemas."""
    transport = SyntheticTransport()
    common = {
        "dataCode": "SYNTHETIC_STATION",
        "elements": "Station_Id_C,Lat,Lon,TEM",
        "orderby": "Station_ID_d:asc",
    }
    routes = [
        ("getSurfEleByTime", {"times": "20260102000000"}, None),
        (
            "getSurfEleByTimeAndStaID",
            {"times": "20260102000000", "staIds": "FAKE001", "limitCnt": 1},
            [("FAKE001", "30.0", "110.0", "280.0")],
        ),
        (
            "getSurfEleByTimeRangeAndStaID",
            {
                "timeRange": "[20260102000000,20260102060000)",
                "staIds": "FAKE001,FAKE002",
            },
            None,
        ),
        (
            "getSurfEleInRectByTime",
            {
                "times": "20260102000000",
                "minLat": "30.0", "maxLat": "31.0",
                "minLon": "110.0", "maxLon": "111.0",
            },
            None,
        ),
    ]
    for interface_id, params, rows in routes:
        transport.register_api(
            "callAPI_to_array2D", interface_id, {**common, **params},
            make_array2d_content(rows=rows),
        )
    transport.register_api(
        "callAPI_to_array2D", "getSurfLatestTime",
        {"dataCode": "SYNTHETIC_STATION", "latestTime": "6"},
        make_array2d_content(
            element_names=["Datetime"], rows=[("20260102000000",)],
        ),
    )
    return make_synthetic_music_client(transport), transport


def check_results(table, single, selected, regional, latest, numeric, transport):
    """Check independent expected values, metadata and request cleanup."""
    expected_rows = [
        ["FAKE001", "30.0", "110.0", "280.0"],
        ["FAKE002", "31.0", "111.0", "281.5"],
    ]
    for result, interface_id in [
        (table, "getSurfEleByTime"),
        (single, "getSurfEleByTimeAndStaID"),
        (selected, "getSurfEleByTimeRangeAndStaID"),
        (regional, "getSurfEleInRectByTime"),
    ]:
        assert isinstance(result, pd.DataFrame)
        assert result.columns.tolist() == ["Station_Id_C", "Lat", "Lon", "TEM"]
        assert result.values.tolist() == (expected_rows[:1] if result is single else expected_rows)
        assert all(isinstance(value, str) for value in result.values.flat)
        assert result.attrs["interface_id"] == interface_id
        assert result.attrs["request_time"] == "20260102000000"
        assert result.attrs["response_time"] == "20260102000001"
    assert table.attrs == {
        "interface_id": "getSurfEleByTime",
        "request_time": "20260102000000",
        "response_time": "20260102000001",
    }
    assert selected.attrs["time_range"] == "[20260102000000,20260102060000)"
    assert latest.columns.tolist() == ["Datetime"]
    assert latest.values.tolist() == [["20260102000000"]]
    assert latest.attrs["interface_id"] == "getSurfLatestTime"
    assert numeric["TEM"].tolist() == [280.0, 281.5]
    assert pd.api.types.is_numeric_dtype(numeric["TEM"])
    assert table["TEM"].tolist() == ["280.0", "281.5"]
    assert len(transport.calls) == 5
    assert len(transport.responses) == 5
    assert all(response.closed for response in transport.responses)


def run_example():
    """Execute the guide's public calls and check their contracts."""
    client, transport = make_station_client()
    common = {
        "data_code": "SYNTHETIC_STATION",
        "elements": "Station_Id_C,Lat,Lon,TEM",
        "client": client,
        "strict": True,
    }
    time = pd.Timestamp("2026-01-02")
    table = retrieve_obs_station(**common, time=time)
    single = retrieve_obs_station(**common, time=time, station="FAKE001", count=1)
    selected = retrieve_obs_station(
        **common, station=["FAKE001", "FAKE002"],
        time=pd.Interval(time, pd.Timestamp("2026-01-02 06:00"), closed="left"),
    )
    regional = retrieve_obs_station(
        **common, time=time,
        region={
            "type": "rect", "start_longitude": 110, "end_longitude": 111,
            "start_latitude": 30, "end_latitude": 31,
        },
    )
    latest = retrieve_obs_station(
        "SYNTHETIC_STATION", time=pd.Timedelta(hours=6), client=client, strict=True,
    )
    numeric = table.copy()
    numeric["TEM"] = pd.to_numeric(numeric["TEM"], errors="raise")
    calls_before = len(transport.calls)
    try:
        retrieve_obs_station(
            "SYNTHETIC_STATION", time=pd.Timedelta(hours=6),
            station="FAKE001", client=client, strict=True,
        )
    except UnsupportedQueryError:
        assert len(transport.calls) == calls_before
    else:
        raise AssertionError("latest-time station filters must fail before a request")
    check_results(table, single, selected, regional, latest, numeric, transport)
    return {
        "table": table, "single": single, "selected": selected,
        "regional": regional, "latest": latest, "numeric": numeric,
    }


if __name__ == "__main__":
    results = run_example()
    for name, result in results.items():
        print(f"\n{name}:\n{result.to_string(index=False)}")
    print(f"\ndtypes:\n{results['table'].dtypes}")
    print(f"\nattrs: {results['table'].attrs}")
    print("\nAll synthetic station contracts passed.")
