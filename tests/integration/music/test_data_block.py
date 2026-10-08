"""Native DataBlock probe, pending a cataloged RetDataBlock service capability."""

import pytest

from nuwe_cmadaas.music import DataBlock
from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("music_data_block"))
def test_registered_case(case, request, integration_profile, low_level_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}; {case['verification_blocker']}")

    capability = low_level_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], capability, request)
    with pytest.warns(UserWarning, match="no verified live-service interface"):
        result = request.getfixturevalue("real_client").callAPI_to_dataBlock(**kwargs)

    assert isinstance(result, DataBlock)
    assert result.ok, f"{case_id}: {result.request.error_code} {result.request.error_message}"
    expected = case["expected_return_contract"]
    assert expected["kind"] == "DataBlock"
    if expected["nonempty_name"]:
        assert isinstance(result.data_name, str) and result.data_name
    assert isinstance(result.data, bytes)
    if expected["nonempty_bytes"]:
        assert 0 < len(result.data) <= capability["max_bytes"]
