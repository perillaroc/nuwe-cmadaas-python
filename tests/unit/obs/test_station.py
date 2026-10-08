import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.music import MusicError
from nuwe_cmadaas.obs import retrieve_obs_station
from tests.fixtures import FakeCMADaaSClient, make_array2d_response


pytestmark = pytest.mark.unit

DATA_CODE = "SYNTHETIC_STATION"
ELEMENTS = "Station_Id_C,Lat,Lon,TEM"
TIME = pd.Timestamp("2026-01-02 00:00:00")
LATER_TIME = pd.Timestamp("2026-01-02 06:00:00")


def make_client(result=None):
    return FakeCMADaaSClient(result or make_array2d_response())


@pytest.mark.parametrize("extra", [
    {"elements": "Datetime"},
    {"station": "54511"},
    {"region": {"type": "region", "admin_codes": "110000"}},
    {"station_level": "011"},
    {"order": "Datetime:desc"},
    {"count": 1},
    {"dataProvinceId": "BABJ"},
    {"family": None},
])
def test_latest_time_rejects_extra_filters_before_request(extra):
    client = make_client()

    with pytest.raises(UnsupportedQueryError, match="latest-time query does not support filters"):
        retrieve_obs_station(data_code=DATA_CODE, time=pd.Timedelta(hours=6), client=client, **extra)

    assert client.calls == []


@pytest.mark.parametrize(
    ("kwargs", "interface_id", "expected_params"),
    [
        (
            {"time": TIME},
            "getSurfEleByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "times": "20260102000000",
            },
        ),
        (
            {"time": [TIME, LATER_TIME]},
            "getSurfEleByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "times": "20260102000000,20260102060000",
            },
        ),
        (
            {"time": pd.Interval(TIME, LATER_TIME, closed="both")},
            "getSurfEleByTimeRange",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "timeRange": "[20260102000000,20260102060000]",
            },
        ),
        (
            {"time": pd.Timedelta(hours=6)},
            "getSurfLatestTime",
            {"dataCode": DATA_CODE, "latestTime": "6"},
        ),
        (
            {"station": "FAKE001"},
            "getSurfEleByStaID",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "staIds": "FAKE001",
            },
        ),
        (
            {"station": 53592},
            "getSurfEleByStaID",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "staIds": 53592,
            },
        ),
        (
            {"station": ["FAKE001", "FAKE002"]},
            "getSurfEleByStaID",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "staIds": "FAKE001,FAKE002",
            },
        ),
        (
            {"time": TIME, "station": ("FAKE001", "FAKE999")},
            "getSurfEleByTimeAndStaIdRange",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "minStaId": "FAKE001",
                "maxStaId": "FAKE999",
                "times": "20260102000000",
            },
        ),
        (
            {
                "time": TIME,
                "region": {
                    "type": "rect",
                    "start_longitude": 112.0,
                    "end_longitude": 110.0,
                    "start_latitude": 32.0,
                    "end_latitude": 30.0,
                },
            },
            "getSurfEleInRectByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "minLat": "30.0",
                "minLon": "110.0",
                "maxLat": "32.0",
                "maxLon": "112.0",
                "times": "20260102000000",
            },
        ),
        (
            {"time": TIME, "region": {"type": "region", "admin_codes": "110000"}},
            "getSurfEleInRegionByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "adminCodes": "110000",
                "times": "20260102000000",
            },
        ),
        (
            {"time": TIME, "region": {"type": "basin", "basin_codes": "SYNTHETIC_BASIN"}},
            "getSurfEleInBasinByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "basinCodes": "SYNTHETIC_BASIN",
                "times": "20260102000000",
            },
        ),
        (
            {"station_level": "011", "time": pd.Interval(TIME, LATER_TIME, closed="both")},
            "getSurfEleByTimeRangeAndStaLevels",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "timeRange": "[20260102000000,20260102060000]",
                "staLevels": "011",
            },
        ),
        (
            {"station_level": ["011", "012"], "time": pd.Interval(TIME, LATER_TIME, closed="both")},
            "getSurfEleByTimeRangeAndStaLevels",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "timeRange": "[20260102000000,20260102060000]",
                "staLevels": "011,012",
            },
        ),
        (
            {"time": TIME, "count": 2},
            "getSurfEleByTime",
            {
                "dataCode": DATA_CODE,
                "elements": ELEMENTS,
                "orderby": "Station_ID_d:asc",
                "times": "20260102000000",
                "limitCnt": 2,
            },
        ),
    ],
)
def test_retrieve_obs_station_builds_request(
    kwargs, interface_id, expected_params
):
    client = make_client()

    result = retrieve_obs_station(
        DATA_CODE,
        elements=None if interface_id == "getSurfLatestTime" else ELEMENTS,
        client=client,
        **kwargs,
    )

    assert isinstance(result, pd.DataFrame)
    assert client.calls == [(interface_id, expected_params)]


def test_retrieve_obs_station_passes_extra_parameters():
    client = make_client()

    result = retrieve_obs_station(
        DATA_CODE,
        elements=ELEMENTS,
        time=TIME,
        client=client,
        eleValueRanges="TEM:270,290",
    )

    assert isinstance(result, pd.DataFrame)
    assert client.calls[0] == (
        "getSurfEleByTime",
        {
            "dataCode": DATA_CODE,
            "elements": ELEMENTS,
            "orderby": "Station_ID_d:asc",
            "times": "20260102000000",
            "eleValueRanges": "TEM:270,290",
        },
    )


def test_retrieve_obs_station_returns_synthetic_music_error():
    client = make_client(
        make_array2d_response(
            error_code=-1234,
            error_message="Synthetic station query failure",
        )
    )

    result = retrieve_obs_station(
        DATA_CODE,
        elements=ELEMENTS,
        time=TIME,
        client=client,
    )

    assert result == MusicError(-1234, "Synthetic station query failure")


@pytest.mark.parametrize("count", [0, -1, 1.5, True])
def test_retrieve_obs_station_rejects_invalid_count_without_request(count):
    client = make_client()

    with pytest.raises((TypeError, ValueError), match="count"):
        retrieve_obs_station(
            DATA_CODE,
            elements=ELEMENTS,
            count=count,
            client=client,
        )

    assert client.calls == []


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({}, id="getSurfEle"),
        pytest.param({"station": ("FAKE001", "FAKE999")}, id="getSurfEleByStaIDRange"),
        pytest.param({"station_level": "011"}, id="getSurfEleByStaLevels"),
        pytest.param({"time": TIME, "station_level": "011"}, id="getSurfEleByTimeAndStaLevels"),
        *[
            pytest.param(kwargs, id=interface_id)
            for region, prefix in [
                ({"type": "rect", "start_longitude": 110, "end_longitude": 111,
                  "start_latitude": 30, "end_latitude": 31}, "getSurfEleInRect"),
                ({"type": "region", "admin_codes": "110000"}, "getSurfEleInRegion"),
                ({"type": "basin", "basin_codes": "CJLY"}, "getSurfEleInBasin"),
            ]
            for kwargs, interface_id in [
                ({"region": region}, prefix),
                ({"region": region, "time": TIME, "station": "FAKE001"},
                 prefix + "ByTimeAndStaID"),
                ({"region": region, "time": pd.Interval(TIME, LATER_TIME, closed="both"),
                  "station": "FAKE001"}, prefix + "ByTimeRangeAndStaID"),
            ]
        ],
    ],
)
def test_removed_station_queries_fail_before_request(kwargs):
    client = make_client()

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_obs_station(DATA_CODE, elements=ELEMENTS, client=client, **kwargs)

    assert client.calls == []
