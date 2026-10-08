"""Every B10 case must reach its cataloged API through retrieve_model_point."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.model import retrieve_model_point
from tests.fixtures import FakeCMADaaSClient, make_array2d_response
from tests.integration.case_registry import load_cases, resolve_case_value


pytestmark = pytest.mark.unit
PROFILE = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "integration/profiles.example.yaml")
    .read_text(encoding="utf-8")
)
BASE_TIME = (pd.Timestamp.now() - pd.Timedelta(days=3)).normalize()
CYCLE_TIME = BASE_TIME + pd.Timedelta(hours=6)
CODE = "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE"
COMMON = {
    "dataCode": CODE,
    "fcstEle": "TEM",
    "time": CYCLE_TIME.strftime("%Y%m%d%H%M%S"),
    "levelType": "103",
    "fcstLevel": "2",
}
EXPECTED = {
    "MP-001": (
        "getNafpEleAtPointByTimeAndLevelAndValidtime",
        {"validTime": "24", "latLons": "39.9/116.4"},
    ),
    "MP-001-multi-point": (
        "getNafpEleAtPointByTimeAndLevelAndValidtime",
        {"validTime": "24", "latLons": "39.9/116.4,31.2/121.5"},
    ),
    "MP-002": (
        "getNafpEleAtPointByTimeAndLevelAndValidtimeRange",
        {"minVT": "6", "maxVT": "24", "latLons": "39.9/116.4"},
    ),
    "MP-003": (
        "getNafpEleByTimeAndLevelAndValidtimeAndStaID",
        {"validTime": "24", "staIds": "54511"},
    ),
    "MP-004": (
        "getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID",
        {"minVT": "6", "maxVT": "24", "staIds": "54511"},
    ),
}


class SyntheticRequest:
    def getfixturevalue(self, name):
        assert name == "model_point_cycle_time"
        return CYCLE_TIME


def test_model_point_cases_cover_all_registered_interfaces():
    cases = load_cases("model_point")
    assert {case["case_id"] for case in cases} == set(EXPECTED)
    assert {case["interface_id"] for case in cases} == {
        interface_id for interface_id, _ in EXPECTED.values()
    }


@pytest.mark.parametrize("case_id", EXPECTED)
def test_model_point_case_reaches_expected_interface_and_parameters(case_id):
    case = next(case for case in load_cases("model_point") if case["case_id"] == case_id)
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_array2d_response())

    retrieve_model_point(**kwargs, client=client)

    assert len(client.calls) == 1
    expected_interface, extra = EXPECTED[case_id]
    assert case["interface_id"] == expected_interface
    assert client.calls[0] == (expected_interface, COMMON | extra)
