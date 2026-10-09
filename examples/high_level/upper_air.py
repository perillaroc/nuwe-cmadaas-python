"""Offline upper-air branches shared with the executable guide.

From the repository root: ``python -m examples.high_level.upper_air``.
All rows are fictional; no credentials or service connection are used.
"""

import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.obs import retrieve_obs_upper_air


REGULAR_ELEMENTS = "Station_Id_d,Lat,Lon,PRS_HWC,GPH,EVSS,TEM"
REGULAR_ROWS = [
    ["FAKE001", "30.0", "110.0", "850", "1500", "4096", "250.0"],
    ["FAKE002", "31.0", "111.0", "700", "3000", "4096", "240.0"],
]


def make_upper_air_client():
    """Register each branch with its own fields and exact MUSIC parameters."""
    transport = SyntheticTransport()

    def register(interface_id, params, elements, rows):
        transport.register_api(
            "callAPI_to_array2D", interface_id, params,
            make_array2d_content(element_names=elements.split(","), rows=rows),
        )

    regular = {"dataCode": "SYNTHETIC_UPPER", "elements": REGULAR_ELEMENTS}
    register("getUparEleByTime", {**regular, "times": "20260102000000"},
             REGULAR_ELEMENTS, REGULAR_ROWS)
    register(
        "getUparEleByTimeAndStaIDAndPress",
        {**regular, "times": "20260102000000", "staIds": "FAKE001",
         "pLayers": "850,700", "limitCnt": 2},
        REGULAR_ELEMENTS,
        [REGULAR_ROWS[0], ["FAKE001", *REGULAR_ROWS[1][1:]]],
    )
    for interface_id, level_params in [
        ("getUparEleByTimeAndHeight", {"hLayers": "1500"}),
        ("getUparEleByTimeAndVertical", {"verticals": "4096"}),
    ]:
        register(interface_id, {**regular, "times": "20260102000000", **level_params},
                 REGULAR_ELEMENTS, REGULAR_ROWS[:1])
    gps_elements = "Station_Id_C,Lat,Lon,TEM"
    gps_rows = [["FAKE001", "30.0", "110.0", "280.0"]]
    register(
        "getUparGpsEleByTimeAndStaID",
        {"elements": gps_elements, "times": "20260102000000", "staIds": "FAKE001"},
        gps_elements, gps_rows,
    )
    register(
        "getUparGpsEleByTimeRangeAndStaID",
        {"dataCode": "SYNTHETIC_GPS", "elements": gps_elements,
         "timeRange": "[20260102000000,20260102010000)", "staIds": "FAKE001"},
        gps_elements, gps_rows,
    )
    register(
        "getUparLightEleInRectByTimeRange",
        {"dataCode": "SYNTHETIC_LIGHT", "elements": "Datetime,Lat,Lon",
         "timeRange": "[20260102000000,20260102010000)",
         "minLat": "30.0", "maxLat": "31.0", "minLon": "110.0", "maxLon": "111.0"},
        "Datetime,Lat,Lon", [["20260102003000", "30.0", "110.0"]],
    )
    register(
        "getUparArdEleByTimeRangeAndHeightRange",
        {"dataCode": "SYNTHETIC_ARD", "elements": "Lat,Lon,Flight_Heigh,TEM",
         "timeRange": "[20260102000000,20260102010000)",
         "minFLayer": 5000, "maxFLayer": 10000},
        "Lat,Lon,Flight_Heigh,TEM",
        [["30.0", "110.0", "6000", "250.0"], ["31.0", "111.0", "9000", "240.0"]],
    )
    register("getUparLatestTime", {"dataCode": "SYNTHETIC_UPPER", "latestTime": "6"},
             "Datetime", [["20260102000000"]])
    return make_synthetic_music_client(transport), transport


def check_results(results, transport):
    """Check branch-specific schema and independent expected values."""
    expected = {
        "regular": ("getUparEleByTime", REGULAR_ELEMENTS, [
            ["FAKE001", "30.0", "110.0", "850", "1500", "4096", "250.0"],
            ["FAKE002", "31.0", "111.0", "700", "3000", "4096", "240.0"],
        ]),
        "pressure": ("getUparEleByTimeAndStaIDAndPress", REGULAR_ELEMENTS, [
            ["FAKE001", "30.0", "110.0", "850", "1500", "4096", "250.0"],
            ["FAKE001", "31.0", "111.0", "700", "3000", "4096", "240.0"],
        ]),
        "height": ("getUparEleByTimeAndHeight", REGULAR_ELEMENTS, [
            ["FAKE001", "30.0", "110.0", "850", "1500", "4096", "250.0"],
        ]),
        "vertical": ("getUparEleByTimeAndVertical", REGULAR_ELEMENTS, [
            ["FAKE001", "30.0", "110.0", "850", "1500", "4096", "250.0"],
        ]),
        "gps": ("getUparGpsEleByTimeAndStaID", "Station_Id_C,Lat,Lon,TEM", [
            ["FAKE001", "30.0", "110.0", "280.0"],
        ]),
        "gps_range": ("getUparGpsEleByTimeRangeAndStaID", "Station_Id_C,Lat,Lon,TEM", [
            ["FAKE001", "30.0", "110.0", "280.0"],
        ]),
        "light": ("getUparLightEleInRectByTimeRange", "Datetime,Lat,Lon", [
            ["20260102003000", "30.0", "110.0"],
        ]),
        "ard": ("getUparArdEleByTimeRangeAndHeightRange", "Lat,Lon,Flight_Heigh,TEM", [
            ["30.0", "110.0", "6000", "250.0"], ["31.0", "111.0", "9000", "240.0"],
        ]),
        "latest": ("getUparLatestTime", "Datetime", [["20260102000000"]]),
    }
    assert results.keys() == expected.keys()
    for name, (interface_id, elements, rows) in expected.items():
        table = results[name]
        assert isinstance(table, pd.DataFrame)
        assert table.columns.tolist() == elements.split(",")
        assert table.shape == (len(rows), len(elements.split(",")))
        assert table.values.tolist() == rows
        assert all(isinstance(value, str) for value in table.values.flat)
        metadata = {
            "interface_id": interface_id,
            "request_time": "20260102000000", "response_time": "20260102000001",
        }
        if name in {"gps_range", "light", "ard"}:
            metadata["time_range"] = "[20260102000000,20260102010000)"
        assert table.attrs == metadata
    assert pd.to_numeric(results["ard"]["Flight_Heigh"]).between(5000, 10000).all()
    assert len(transport.calls) == 9
    assert len(transport.responses) == 9
    assert all(response.closed for response in transport.responses)


def run_example():
    """Run conventional, GPS, lightning, aircraft and latest-time calls."""
    client, transport = make_upper_air_client()
    time = pd.Timestamp("2026-01-02")
    interval = pd.Interval(time, time + pd.Timedelta(hours=1), closed="left")
    regular = {
        "data_code": "SYNTHETIC_UPPER", "elements": REGULAR_ELEMENTS,
        "time": time, "client": client, "strict": True,
    }
    results = {
        "regular": retrieve_obs_upper_air(**regular),
        "pressure": retrieve_obs_upper_air(
            **regular, station="FAKE001", level_type="pl", level=[850, 700], count=2,
        ),
        "height": retrieve_obs_upper_air(**regular, level_type="gh", level=1500),
        "vertical": retrieve_obs_upper_air(**regular, level_type="vertical", level=4096),
    }
    for name, selector in [("gps", time), ("gps_range", interval)]:
        results[name] = retrieve_obs_upper_air(
            "SYNTHETIC_GPS", elements="Station_Id_C,Lat,Lon,TEM",
            time=selector, station="FAKE001", interface_data_type="UparGps",
            client=client, strict=True,
        )
    results["light"] = retrieve_obs_upper_air(
        "SYNTHETIC_LIGHT", elements="Datetime,Lat,Lon", time=interval,
        region={"type": "rect", "start_longitude": 110, "end_longitude": 111,
                "start_latitude": 30, "end_latitude": 31},
        interface_data_type="UparLight", client=client, strict=True,
    )
    results["ard"] = retrieve_obs_upper_air(
        "SYNTHETIC_ARD", elements="Lat,Lon,Flight_Heigh,TEM", time=interval,
        level_type="fl", level=pd.Interval(5000, 10000, closed="both"),
        client=client, strict=True,
    )
    results["latest"] = retrieve_obs_upper_air(
        "SYNTHETIC_UPPER", time=pd.Timedelta(hours=6), client=client, strict=True,
    )
    for selectors, error_type in [
        ({"time": time, "elements": REGULAR_ELEMENTS, "level_type": "pl"}, ValueError),
        ({"time": time, "elements": REGULAR_ELEMENTS,
          "level_type": "fl", "level": 6000}, UnsupportedQueryError),
        ({"time": pd.Timedelta(hours=6), "station": "FAKE001"}, UnsupportedQueryError),
    ]:
        calls_before = len(transport.calls)
        try:
            retrieve_obs_upper_air(
                "SYNTHETIC_UPPER", client=client, strict=True, **selectors,
            )
        except error_type:
            assert len(transport.calls) == calls_before
        else:
            raise AssertionError(f"invalid selectors must fail before a request: {selectors}")
    check_results(results, transport)
    return results


if __name__ == "__main__":
    for name, table in run_example().items():
        print(f"\n{name}:\n{table.to_string(index=False)}")
        print(f"attrs: {table.attrs}")
    print("\nAll synthetic upper-air contracts passed.")
