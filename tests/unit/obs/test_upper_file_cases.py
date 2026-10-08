"""Upper-air file cases reach the cataloged interfaces through their wrapper."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface
from nuwe_cmadaas.obs import download_obs_upper_air_file
from tests.fixtures import FakeCMADaaSClient, make_files_info_response
from tests.integration.case_registry import load_cases, resolve_case_value
from tests.integration.file_download import BoundedDownloadClient
from tests.unit.obs.test_file import REMOVED_COMBINATIONS


pytestmark = pytest.mark.unit
PROFILE = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "integration/profiles.example.yaml")
    .read_text(encoding="utf-8")
)


class SyntheticRequest:
    def getfixturevalue(self, name):
        base_time = (pd.Timestamp.now() - pd.Timedelta(days=2)).normalize()
        return {
            "recent_file_time": base_time,
            "recent_file_short_time_range": pd.Interval(
                base_time, base_time + pd.Timedelta(hours=1), closed="both"
            ),
            "online_output_dir": Path("/tmp/synthetic-upper-file-case"),
        }[name]


@pytest.mark.parametrize(
    "case", load_cases("obs_upper_file"), ids=lambda case: case["case_id"]
)
def test_upper_file_case_reaches_declared_interface(case):
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_files_info_response())

    paths = download_obs_upper_air_file(**kwargs, client=client)

    assert paths == [kwargs["output_dir"] / "synthetic.bin"]
    assert len(client.calls) == 1
    interface_id, params = client.calls[0]
    assert interface_id == case["interface_id"]
    assert params["dataCode"] == dataset["data_code"]
    assert params["limitCnt"] == dataset["max_files"]
    assert ("timeRange" in params) == ("time_range" in case["query_features"])
    assert ("times" in params) == ("time" in case["query_features"])
    assert ("staIds" in params) == ("station" in case["query_features"])
    if "station" in case["query_features"]:
        assert params["staIds"] == dataset["station_id"]


REMOVED_UPPER_COMBINATIONS = [
    (features, kwargs) for features, kwargs in REMOVED_COMBINATIONS
    if set(features) != {"station", "time"}
]
assert len(REMOVED_UPPER_COMBINATIONS) == 23


@pytest.mark.parametrize(("features", "kwargs"), REMOVED_UPPER_COMBINATIONS)
def test_catalog_absent_upper_file_combination_rejects_before_request(
    tmp_path, features, kwargs
):
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface("obs_upper_file", features)
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        download_obs_upper_air_file(
            "SYNTHETIC_UPPER", output_dir=tmp_path, client=client, **kwargs
        )

    assert client.calls == []


def test_upper_file_preflight_blocks_large_download(tmp_path):
    listing = make_files_info_response(file_infos=[{
        "file_name": "synthetic.bin", "file_url": "https://synthetic.invalid/data.bin",
        "size": "11",
    }])

    class RecordingClient:
        def __init__(self):
            self.calls = []

        def callAPI_to_fileList(self, interface_id, params):
            self.calls.append(("list", interface_id))
            return listing

        def callAPI_to_downFile(self, interface_id, params, file_dir):
            self.calls.append(("download", interface_id))
            return listing

    underlying = RecordingClient()
    client = BoundedDownloadClient(underlying, max_files=1, max_total_bytes=10)

    with pytest.raises(AssertionError, match="exceeds"):
        download_obs_upper_air_file(
            "SYNTHETIC_UPPER", time=pd.Timestamp.now().normalize(),
            output_dir=tmp_path, client=client,
        )

    assert underlying.calls == [("list", "getUparFileByTime")]
