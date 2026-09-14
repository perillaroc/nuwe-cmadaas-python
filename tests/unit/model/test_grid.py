import pandas as pd
import pytest
import xarray as xr

from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.model.grid import _get_interface_id
from nuwe_cmadaas.music import MusicError
from tests.fixtures import FakeCMADaaSClient, make_grid_array2d_response


pytestmark = pytest.mark.unit

DATA_CODE = "SYNTHETIC_MODEL"
PARAMETER = "synthetic_temperature"
TIME = pd.Timestamp("2026-01-02 00:00:00")
RECTANGLE = {
    "type": "rect",
    "start_longitude": 112.0,
    "end_longitude": 110.0,
    "start_latitude": 32.0,
    "end_latitude": 30.0,
}


def test_retrieve_model_grid_builds_forecast_request():
    client = FakeCMADaaSClient(make_grid_array2d_response())

    result = retrieve_model_grid(
        DATA_CODE,
        parameter=PARAMETER,
        start_time=TIME,
        forecast_time="24h",
        level_type=100,
        level=850,
        region=RECTANGLE,
        number=3,
        client=client,
    )

    assert isinstance(result, xr.DataArray)
    assert client.calls == [
        (
            "getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember",
            {
                "dataCode": DATA_CODE,
                "fcstEle": PARAMETER,
                "levelType": "100",
                "fcstLevel": "850",
                "time": "20260102000000",
                "validTime": "24",
                "minLat": "30.0",
                "minLon": "110.0",
                "maxLat": "32.0",
                "maxLon": "112.0",
                "fcstMember": 3,
            },
        )
    ]


def test_retrieve_model_grid_builds_analysis_request():
    client = FakeCMADaaSClient(make_grid_array2d_response())

    result = retrieve_model_grid(
        DATA_CODE,
        parameter=PARAMETER,
        start_time=TIME,
        forecast_time=pd.Timedelta(hours=0),
        data_type="analysis",
        client=client,
    )

    assert isinstance(result, xr.DataArray)
    assert client.calls == [
        (
            "getNafpAnaEleGridByTimeAndValidtime",
            {
                "dataCode": DATA_CODE,
                "fcstEle": PARAMETER,
                "time": "20260102000000",
                "validTime": "0",
            },
        )
    ]


def test_retrieve_model_grid_builds_minimal_forecast_request():
    client = FakeCMADaaSClient(make_grid_array2d_response())

    result = retrieve_model_grid(
        DATA_CODE,
        parameter=PARAMETER,
        client=client,
    )

    assert isinstance(result, xr.DataArray)
    assert client.calls == [
        (
            "getNafpEleGrid",
            {"dataCode": DATA_CODE, "fcstEle": PARAMETER},
        )
    ]


def test_retrieve_model_grid_returns_synthetic_music_error():
    client = FakeCMADaaSClient(
        make_grid_array2d_response(
            error_code=-3234,
            error_message="Synthetic model query failure",
        )
    )

    result = retrieve_model_grid(
        DATA_CODE,
        parameter=PARAMETER,
        client=client,
    )

    assert result == MusicError(-3234, "Synthetic model query failure")


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            {
                "name": "getNafpEleGrid",
                "region": "Rect",
                "time": "Time",
                "level": "Level",
                "valid_time": "Validtime",
                "number": "FcstMember",
            },
            "getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember",
        ),
        (
            {
                "name": "getNafpEleGrid",
                "region": None,
                "time": None,
                "level": None,
                "valid_time": None,
                "number": None,
            },
            "getNafpEleGrid",
        ),
    ],
)
def test_get_interface_id(config, expected):
    assert _get_interface_id(config) == expected
