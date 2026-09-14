import pandas as pd
import pytest
import xarray as xr

from nuwe_cmadaas.music import MusicError
from nuwe_cmadaas.obs import retrieve_obs_grid
from tests.fixtures import FakeCMADaaSClient, make_grid_array2d_response


pytestmark = pytest.mark.unit

DATA_CODE = "SYNTHETIC_GRID"
PARAMETER = "synthetic_temperature"
TIME = pd.Timestamp("2026-01-02 00:00:00")
LATER_TIME = pd.Timestamp("2026-01-02 06:00:00")
RECTANGLE = {
    "type": "rect",
    "start_longitude": 112.0,
    "end_longitude": 110.0,
    "start_latitude": 32.0,
    "end_latitude": 30.0,
}


@pytest.mark.parametrize(
    ("time", "interface_id", "time_params"),
    [
        (TIME, "getSurfEleGridByTime", {"time": "20260102000000"}),
        (
            [TIME, LATER_TIME],
            "getSurfEleGridByTime",
            {"times": "20260102000000,20260102060000"},
        ),
        (
            pd.Interval(TIME, LATER_TIME, closed="right"),
            "getSurfEleGridByTimeRange",
            {"timeRange": ")20260102000000,20260102060000]"},
        ),
    ],
)
def test_retrieve_obs_grid_builds_time_request(
    time, interface_id, time_params
):
    client = FakeCMADaaSClient(make_grid_array2d_response())

    result = retrieve_obs_grid(
        DATA_CODE,
        parameter=PARAMETER,
        time=time,
        client=client,
    )

    assert isinstance(result, xr.DataArray)
    assert client.calls == [
        (
            interface_id,
            {"dataCode": DATA_CODE, "fcstEle": PARAMETER, **time_params},
        )
    ]


def test_retrieve_obs_grid_builds_rectangle_request():
    client = FakeCMADaaSClient(make_grid_array2d_response())

    result = retrieve_obs_grid(
        DATA_CODE,
        parameter=PARAMETER,
        time=TIME,
        region=RECTANGLE,
        client=client,
    )

    assert isinstance(result, xr.DataArray)
    assert client.calls == [
        (
            "getSurfEleGridInRectByTime",
            {
                "dataCode": DATA_CODE,
                "fcstEle": PARAMETER,
                "time": "20260102000000",
                "minLat": "30.0",
                "minLon": "110.0",
                "maxLat": "32.0",
                "maxLon": "112.0",
            },
        )
    ]


def test_retrieve_obs_grid_returns_synthetic_music_error():
    client = FakeCMADaaSClient(
        make_grid_array2d_response(
            error_code=-2234,
            error_message="Synthetic grid query failure",
        )
    )

    result = retrieve_obs_grid(
        DATA_CODE,
        parameter=PARAMETER,
        time=TIME,
        client=client,
    )

    assert result == MusicError(-2234, "Synthetic grid query failure")
