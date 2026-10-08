"""Native serialized strings for each service-supported output format."""

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("music_serialized_str"))
def test_registered_case(case, request, integration_profile, low_level_profile, online_output_dir):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    capability = low_level_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], capability, request)
    expected = case["expected_return_contract"]
    fmt = kwargs["data_format"]
    assert fmt == expected["format"] and fmt in capability["formats"]
    assert "dataFormat" not in kwargs["params"]
    before = set(Path(online_output_dir).iterdir())

    content = request.getfixturevalue("real_client").callAPI_to_serializedStr(**kwargs)

    assert expected["kind"] == "str"
    assert isinstance(content, str)
    assert 0 < len(content) <= expected["max_chars"]
    assert kwargs["params"]["dataFormat"] == fmt
    assert not content.startswith(("getway error:", "parse getway return string error:", "Error retrieving data"))
    assert set(Path(online_output_dir).iterdir()) == before, "serializedStr must not write a file"
    cycle_time = kwargs["params"]["time"]

    if fmt == "json":
        payload = json.loads(content)
        assert str(payload["returnCode"]) == "0"
        assert len(payload["DS"]) == 1
        assert payload["DS"][0]["datetime"] == cycle_time
        assert "TEM_103" in payload["DS"][0]
    elif fmt == "xml":
        root = ET.fromstring(content)
        assert root.attrib["returnCode"] == "0"
        row = root.find("R")
        assert row is not None and row.attrib["datetime"] == cycle_time
        assert "TEM_103" in row.attrib
    elif fmt == "text":
        assert 'returnCode="0"' in content
        assert "TEM_103" in content and cycle_time in content
        assert content.count("\n") >= 2
    elif fmt == "html":
        assert content.startswith("<table")
        assert "<tbody>" in content and "</table>" in content
        assert cycle_time in content
    else:
        pytest.fail(f"Unexpected format in B14 case: {fmt}")
