"""The three cataloged surface-file cases reach their declared interfaces."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.obs import download_obs_file
from tests.fixtures import FakeCMADaaSClient, make_files_info_response
from tests.integration.case_registry import load_cases, resolve_case_value


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
            "online_output_dir": Path("/tmp/synthetic-file-case"),
        }[name]


@pytest.mark.parametrize(
    "case", load_cases("obs_file"), ids=lambda case: case["case_id"]
)
def test_file_case_reaches_declared_interface(case):
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_files_info_response())

    paths = download_obs_file(**kwargs, client=client)

    assert paths == [kwargs["output_dir"] / "synthetic.bin"]
    assert len(client.calls) == 1
    interface_id, params = client.calls[0]
    assert interface_id == case["interface_id"]
    assert params["dataCode"] == dataset["data_code"]
    assert params["limitCnt"] == dataset["max_files"]
    if "time_range" in case["query_features"]:
        assert "timeRange" in params
    else:
        assert "times" in params
    if "station" in case["query_features"]:
        assert params["staIds"] == dataset["station_id"]
