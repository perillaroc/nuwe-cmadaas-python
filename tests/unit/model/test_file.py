from datetime import datetime

import pandas as pd
import pytest

from nuwe_cmadaas.model import download_model_file
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from tests.fixtures import FakeCMADaaSClient, make_files_info_response


pytestmark = pytest.mark.unit


@pytest.mark.parametrize("parameter", [None, ["Datetime"]])
def test_download_model_file_rejects_latest_time_before_request(tmp_path, parameter):
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises(UnsupportedQueryError, match="returns a Datetime table"):
        download_model_file(
            "SYNTHETIC_MODEL",
            parameter=parameter,
            start_time=pd.Timedelta(hours=6),
            output_dir=tmp_path,
            client=client,
        )

    assert client.calls == []


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
