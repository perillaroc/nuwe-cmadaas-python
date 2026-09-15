from datetime import timedelta

import pandas as pd
import pytest

from nuwe_cmadaas.model import retrieve_model_point
from tests.fixtures import FakeCMADaaSClient, make_array2d_response


pytestmark = pytest.mark.unit


def make_client():
    return FakeCMADaaSClient(make_array2d_response())


@pytest.mark.parametrize(
    "forecast_time", ["24h", pd.Timedelta(hours=24), timedelta(hours=24)]
)
def test_retrieve_model_point_accepts_string_and_timedelta_leads(forecast_time):
    client = make_client()

    result = retrieve_model_point(
        "SYNTHETIC_MODEL",
        "TEM",
        pd.Timestamp("2026-01-02"),
        forecast_time,
        level_type=100,
        level=850,
        point=(30.0, 110.0),
        client=client,
    )

    assert result is not None
    assert client.calls[0][0] == "getNafpEleAtPointByTimeAndLevelAndValidtime"
    assert client.calls[0][1]["validTime"] == "24"


def test_retrieve_model_point_accepts_forecast_lead_range():
    client = make_client()

    retrieve_model_point(
        "SYNTHETIC_MODEL",
        "TEM",
        pd.Timestamp("2026-01-02"),
        ("6h", pd.Timedelta(hours=24)),
        level_type=100,
        level=850,
        point=(30.0, 110.0),
        client=client,
    )

    assert client.calls[0][1]["minVT"] == "6"
    assert client.calls[0][1]["maxVT"] == "24"


@pytest.mark.parametrize(
    "forecast_time",
    [24, "not-a-duration", ("6h",), ("24h", "6h"), pd.Timedelta(minutes=30)],
)
def test_retrieve_model_point_rejects_invalid_forecast_time_without_request(
    forecast_time,
):
    client = make_client()

    with pytest.raises((TypeError, ValueError), match="forecast_time"):
        retrieve_model_point(
            "SYNTHETIC_MODEL",
            "TEM",
            pd.Timestamp("2026-01-02"),
            forecast_time,
            level_type=100,
            level=850,
            point=(30.0, 110.0),
            client=client,
        )

    assert client.calls == []


def test_retrieve_model_point_rejects_mutually_exclusive_point_and_station():
    with pytest.raises(ValueError, match="point and station"):
        retrieve_model_point(
            "SYNTHETIC_MODEL",
            "TEM",
            pd.Timestamp("2026-01-02"),
            "24h",
            level_type=100,
            level=850,
            point=(30.0, 110.0),
            station="FAKE001",
            client=make_client(),
        )
