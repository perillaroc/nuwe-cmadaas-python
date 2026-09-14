from pathlib import Path

import pandas as pd
import pytest

from nuwe_cmadaas.obs import download_obs_file
from tests.fixtures import FakeCMADaaSClient, make_files_info_response


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("station", "interface_id", "station_params"),
    [
        ("FAKE001", "getSurfFileByStaID", {"staIds": "FAKE001"}),
        (53592, "getSurfFileByStaID", {"staIds": 53592}),
        ([53592, "FAKE001"], "getSurfFileByStaID", {"staIds": "53592,FAKE001"}),
        ((53592, 53600), "getSurfFileByStaIDRange", {"minStaId": 53592, "maxStaId": 53600}),
    ],
)
def test_download_obs_file_accepts_integer_station_forms(
    tmp_path, station, interface_id, station_params
):
    client = FakeCMADaaSClient(make_files_info_response())

    result = download_obs_file(
        "SYNTHETIC_STATION",
        station=station,
        output_dir=tmp_path,
        client=client,
    )

    assert result == [Path(tmp_path, "synthetic.bin")]
    assert client.calls == [
        (interface_id, {"dataCode": "SYNTHETIC_STATION", **station_params})
    ]


def test_download_obs_file_latest_time_does_not_delete_missing_optional_keys(tmp_path):
    client = FakeCMADaaSClient(make_files_info_response())

    download_obs_file(
        "SYNTHETIC_STATION",
        time=pd.Timedelta(hours=6),
        output_dir=tmp_path,
        client=client,
    )

    assert client.calls == [
        (
            "getSurfLatestTime",
            {"dataCode": "SYNTHETIC_STATION", "latestTime": "6"},
        )
    ]


@pytest.mark.parametrize("count", [0, -1, 1.5, True])
def test_download_obs_file_rejects_invalid_count_without_request(tmp_path, count):
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises((TypeError, ValueError), match="count"):
        download_obs_file(
            "SYNTHETIC_STATION",
            count=count,
            output_dir=tmp_path,
            client=client,
        )

    assert client.calls == []
