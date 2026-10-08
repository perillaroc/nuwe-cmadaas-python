import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import INTERFACE_SPECS, UnsupportedQueryError, resolve_interface
from nuwe_cmadaas.obs import retrieve_obs_upper_air
from tests.fixtures import FakeCMADaaSClient, make_array2d_response


pytestmark = pytest.mark.unit


def test_retrieve_obs_upper_air_latest_time_does_not_delete_missing_keys():
    client = FakeCMADaaSClient(make_array2d_response())

    retrieve_obs_upper_air(
        time=pd.Timedelta(hours=6),
        client=client,
    )

    assert client.calls == [
        (
            "getUparLatestTime",
            {"dataCode": "UPAR_GLB_MUL_FTM", "latestTime": "6"},
        )
    ]


@pytest.mark.parametrize(
    "kwargs",
    [{"level_type": "pl"}, {"level": 850}],
)
def test_retrieve_obs_upper_air_requires_level_pair(kwargs):
    client = FakeCMADaaSClient(make_array2d_response())

    with pytest.raises(ValueError, match="level_type and level"):
        retrieve_obs_upper_air(client=client, **kwargs)

    assert client.calls == []


def test_retrieve_obs_upper_air_ard_uses_cataloged_range_parameters():
    client = FakeCMADaaSClient(make_array2d_response())

    retrieve_obs_upper_air(
        data_code="UPAR_ARD_G_MUT_AMD",
        elements="Lat,Lon,TEM",
        time=pd.Interval(pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-02 01:00"), closed="both"),
        level_type="fl",
        level=pd.Interval(5000, 10000),
        client=client,
    )

    assert client.calls == [(
        "getUparArdEleByTimeRangeAndHeightRange",
        {
            "dataCode": "UPAR_ARD_G_MUT_AMD",
            "elements": "Lat,Lon,TEM",
            "timeRange": "[20260102000000,20260102010000]",
            "minFLayer": 5000,
            "maxFLayer": 10000,
        },
    )]


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"station": "54511"},
        {"interface_data_type": "UparGps", "time": pd.Timestamp("2026-01-02")},
        {"interface_data_type": "UparLight", "time": pd.Timestamp("2026-01-02")},
        {"level_type": "fl", "level": 5000, "time": pd.Timestamp("2026-01-02")},
    ],
)
def test_catalog_absent_upper_air_combinations_fail_before_request(kwargs):
    client = FakeCMADaaSClient(make_array2d_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_obs_upper_air(client=client, **kwargs)

    assert client.calls == []


# The 17 feature shapes in the old high-air registry were generated for each
# ordinary/GPS/Light family. The 2026-10-07 catalog retains only 14 of 51.
LEGACY_UPPER_FEATURES = {
    frozenset(features) for features in (
        (), ("time",), ("time_range",), ("station",), ("station_range",),
        ("station_level",), ("region",), ("region", "time"),
        ("region", "time_range"), ("time", "station"),
        ("time_range", "station"), ("time", "station_level"),
        ("time_range", "station_level"), ("time", "level_press"),
        ("time", "level_height"), ("time", "level_vertical"),
        ("time", "station", "level_press"),
    )
}
UPPER_TYPES = {
    "obs_upper": "Upar",
    "obs_upper_gps": "UparGps",
    "obs_upper_light": "UparLight",
}
REGISTERED_UPPER_FEATURES = {
    family: {spec.query_features for spec in INTERFACE_SPECS if spec.family == family}
    for family in UPPER_TYPES
}
REMOVED_UPPER_FEATURES = [
    (family, features)
    for family in UPPER_TYPES
    for features in LEGACY_UPPER_FEATURES - REGISTERED_UPPER_FEATURES[family]
]
assert len(REMOVED_UPPER_FEATURES) == 37


@pytest.mark.parametrize(("family", "features"), REMOVED_UPPER_FEATURES)
def test_all_removed_upper_air_combinations_reject_before_request(family, features):
    now = pd.Timestamp("2026-01-02")
    kwargs = {
        "data_code": "SYNTHETIC_UPPER", "elements": "TEM",
        "interface_data_type": UPPER_TYPES[family],
    }
    if "time" in features:
        kwargs["time"] = now
    if "time_range" in features:
        kwargs["time"] = pd.Interval(now, now + pd.Timedelta(hours=1))
    if "station" in features:
        kwargs["station"] = "54511"
    if "station_range" in features:
        kwargs["station"] = ("54511", "54512")
    if "station_level" in features:
        kwargs["station_level"] = "011"
    if "region" in features:
        kwargs["region"] = {
            "type": "rect", "start_longitude": 110, "end_longitude": 111,
            "start_latitude": 30, "end_latitude": 31,
        }
    if "level_press" in features:
        kwargs.update(level_type="pl", level=850)
    if "level_height" in features:
        kwargs.update(level_type="gh", level=5000)
    if "level_vertical" in features:
        kwargs.update(level_type="vertical", level=4096)
    client = FakeCMADaaSClient(make_array2d_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface(family, features)
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_obs_upper_air(client=client, **kwargs)
    assert client.calls == []


def test_removed_ard_single_height_rejects_before_request():
    client = FakeCMADaaSClient(make_array2d_response())
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface("obs_upper_ard", {"time", "level_height"})
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_obs_upper_air(
            data_code="SYNTHETIC_UPPER", elements="TEM",
            time=pd.Timestamp("2026-01-02"), level_type="fl", level=5000,
            client=client,
        )
    assert client.calls == []
