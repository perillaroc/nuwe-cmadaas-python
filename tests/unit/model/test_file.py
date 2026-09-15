from pathlib import Path
from datetime import datetime

import pandas as pd
import pytest

from nuwe_cmadaas.model import download_model_file
from tests.fixtures import FakeCMADaaSClient, make_files_info_response


pytestmark = pytest.mark.unit


def test_download_model_file_latest_time_does_not_delete_missing_elements(tmp_path):
    client = FakeCMADaaSClient(make_files_info_response())

    result = download_model_file(
        "SYNTHETIC_MODEL",
        start_time=pd.Timedelta(hours=6),
        output_dir=tmp_path,
        client=client,
    )

    assert result == [Path(tmp_path, "synthetic.bin")]
    assert client.calls == [
        (
            "getNafpLatestTime",
            {"dataCode": "SYNTHETIC_MODEL", "latestTime": "6"},
        )
    ]


def test_download_model_file_accepts_standard_datetime_start_time(tmp_path):
    client = FakeCMADaaSClient(make_files_info_response())

    download_model_file(
        "SYNTHETIC_MODEL",
        start_time=datetime(2026, 1, 2),
        output_dir=tmp_path,
        client=client,
    )

    assert client.calls == [
        (
            "getNafpFileByTime",
            {"dataCode": "SYNTHETIC_MODEL", "time": "20260102000000"},
        )
    ]
