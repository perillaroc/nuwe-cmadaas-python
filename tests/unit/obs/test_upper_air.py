import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import UnsupportedQueryError
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
