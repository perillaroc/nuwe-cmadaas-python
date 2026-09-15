from datetime import datetime, timedelta

import pandas as pd
import pytest

from nuwe_cmadaas.util import (
    NormalizedRegion,
    NormalizedStation,
    NormalizedTime,
    forecast_hours,
    forecast_hour_range,
    normalize_level,
    normalize_region,
    normalize_station,
    normalize_time_filter,
    station_filter_params,
    time_filter_params,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        (pd.Timestamp("2026-01-02 00:00:00"), "single"),
        (datetime(2026, 1, 2), "single"),
        ([datetime(2026, 1, 2), pd.Timestamp("2026-01-02 06:00:00")], "multiple"),
        ((pd.Timestamp("2026-01-02"), datetime(2026, 1, 2, 6)), "multiple"),
        (pd.Interval(pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-02 06:00:00")), "range"),
        (pd.Timedelta(hours=6), "latest"),
        (timedelta(hours=6), "latest"),
    ],
)
def test_normalize_time_filter_accepts_supported_python_and_pandas_forms(value, kind):
    result = normalize_time_filter(value)

    assert isinstance(result, NormalizedTime)
    assert result.kind == kind


@pytest.mark.parametrize(
    "value",
    [[], ["2026-01-02"], pd.Timedelta(minutes=30), object()],
)
def test_normalize_time_filter_rejects_invalid_values(value):
    with pytest.raises((TypeError, ValueError), match="time"):
        normalize_time_filter(value)


def test_time_filter_params_preserves_music_time_parameter_names():
    normalized, params = time_filter_params(
        datetime(2026, 1, 2), single_key="times"
    )

    assert normalized.kind == "single"
    assert params == {"times": "20260102000000"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("24h", 24),
        (pd.Timedelta(hours=24), 24),
        (timedelta(hours=24), 24),
    ],
)
def test_forecast_hours_accepts_standard_and_pandas_durations(value, expected):
    assert forecast_hours(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (("6h", "24h"), (6, 24)),
        ((pd.Timedelta(hours=0), pd.Timedelta(hours=0)), (0, 0)),
    ],
)
def test_forecast_hour_range_normalizes_boundary_values(value, expected):
    assert forecast_hour_range(value) == expected


@pytest.mark.parametrize(
    "value",
    [[], ["850", object()], object()],
)
def test_normalize_level_rejects_invalid_values(value):
    with pytest.raises((TypeError, ValueError), match="level"):
        normalize_level(value)


@pytest.mark.parametrize(
    "value",
    [850, 850.0, "850", [850, 700], (850, 700), pd.Interval(500, 850)],
)
def test_normalize_level_accepts_supported_forms(value):
    assert normalize_level(value) is not None


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        ("FAKE001", "id"),
        (53592, "id"),
        (["FAKE001", 53592], "ids"),
        ((53592, 53600), "range"),
    ],
)
def test_normalize_station_accepts_scalar_list_and_range(value, kind):
    result = normalize_station(value)

    assert isinstance(result, NormalizedStation)
    assert result.kind == kind


@pytest.mark.parametrize("value", [[], [""], (), (1,), [object()]])
def test_normalize_station_rejects_invalid_values(value):
    with pytest.raises((TypeError, ValueError), match="station"):
        normalize_station(value)


def test_station_filter_params_encodes_all_station_forms():
    assert station_filter_params(["FAKE001", 53592])[1] == {
        "staIds": "FAKE001,53592"
    }
    assert station_filter_params((53592, 53600))[1] == {
        "minStaId": 53592,
        "maxStaId": 53600,
    }


def test_normalize_region_normalizes_reversed_rectangle():
    result = normalize_region(
        {
            "type": "rect",
            "start_longitude": 112,
            "end_longitude": 110,
            "start_latitude": 32,
            "end_latitude": 30,
        }
    )

    assert isinstance(result, NormalizedRegion)
    assert result.kind == "rect"
    assert result.value == (30.0, 110.0, 32.0, 112.0)


@pytest.mark.parametrize(
    ("region", "kind", "value"),
    [
        ({"type": "region", "admin_codes": 110000}, "region", "110000"),
        ({"type": "region", "admin_codes": ["110000", "120000"]}, "region", "110000,120000"),
        ({"type": "basin", "basin_codes": "CJLY"}, "basin", "CJLY"),
    ],
)
def test_normalize_region_accepts_code_forms(region, kind, value):
    result = normalize_region(region)

    assert result.kind == kind
    assert result.value == value


@pytest.mark.parametrize(
    "region",
    [
        {"type": "rect", "start_longitude": 181, "end_longitude": 110,
         "start_latitude": 30, "end_latitude": 32},
        {"type": "rect", "start_longitude": 110, "end_longitude": 112,
         "start_latitude": float("nan"), "end_latitude": 32},
        {"type": "region", "admin_codes": []},
    ],
)
def test_normalize_region_rejects_invalid_values(region):
    with pytest.raises((TypeError, ValueError), match="region"):
        normalize_region(region)
