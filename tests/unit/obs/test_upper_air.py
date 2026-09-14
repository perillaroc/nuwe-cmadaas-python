import pandas as pd
import pytest

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
            "getSurfLatestTime",
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
