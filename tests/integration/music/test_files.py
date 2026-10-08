"""Bounded native file listing, downloading, and formatted file creation."""

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from nuwe_cmadaas.music import FileInfo, FilesInfo
from tests.integration.case_registry import case_parameters, resolve_case_value


def _case_kwargs(case, request, integration_profile, low_level_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")
    capability = low_level_profile(case["profile_key"])
    return resolve_case_value(case["public_kwargs"], capability, request), capability


def _assert_listing(result, case, *, max_files, max_total_bytes):
    assert isinstance(result, FilesInfo)
    assert result.ok, f"{case['case_id']}: {result.request.error_code} {result.request.error_message}"
    assert result.request.error_code == 0
    assert 0 < len(result.files_info) <= max_files
    for info in result.files_info:
        assert isinstance(info, FileInfo)
        assert info.file_name and Path(info.file_name).name == info.file_name
        assert "\\" not in info.file_name
        assert info.file_name.endswith("." + case["expected_return_contract"]["file_suffix"])
        assert info.suffix == case["expected_return_contract"]["file_suffix"]
        assert info.file_url
        assert info.size.isdecimal() and int(info.size) > 0
    assert len({info.file_name for info in result.files_info}) == len(result.files_info)
    assert sum(int(info.size) for info in result.files_info) <= max_total_bytes


@pytest.mark.parametrize("case", case_parameters("music_file_list"))
def test_file_list(case, request, integration_profile, low_level_profile, online_output_dir):
    kwargs, capability = _case_kwargs(case, request, integration_profile, low_level_profile)
    assert not list(online_output_dir.iterdir())
    result = request.getfixturevalue("real_client").callAPI_to_fileList(**kwargs)

    assert case["expected_return_contract"]["kind"] == "FilesInfo"
    limits = integration_profile["download_limits"]
    _assert_listing(
        result, case,
        max_files=min(capability["max_files"], limits["max_files"]),
        max_total_bytes=limits["max_total_bytes"],
    )
    assert not list(online_output_dir.iterdir()), "fileList must not download files"


@pytest.mark.parametrize("case", case_parameters("music_down_file"))
def test_down_file(case, request, integration_profile, low_level_profile):
    kwargs, capability = _case_kwargs(case, request, integration_profile, low_level_profile)
    limits = integration_profile["download_limits"]
    assert limits["preflight_file_list"] is True
    assert type(limits["max_files"]) is int and limits["max_files"] > 0
    assert type(limits["max_total_bytes"]) is int and limits["max_total_bytes"] > 0
    output_dir = Path(kwargs["file_dir"])
    assert not list(output_dir.iterdir())
    assert kwargs["overwrite"] is False
    client = request.getfixturevalue("real_client")

    # Use the exact native query for preflight before any binary transfer.
    listing = client.callAPI_to_fileList(kwargs["interface_id"], kwargs["params"].copy())
    max_files = min(capability["max_files"], limits["max_files"])
    _assert_listing(
        listing, case, max_files=max_files, max_total_bytes=limits["max_total_bytes"]
    )
    result = client.callAPI_to_downFile(**kwargs)
    _assert_listing(
        result, case, max_files=max_files, max_total_bytes=limits["max_total_bytes"]
    )
    assert {info.file_name for info in result.files_info} == {
        info.file_name for info in listing.files_info
    }
    assert {path.name for path in output_dir.iterdir()} == {
        info.file_name for info in result.files_info
    }
    for info in result.files_info:
        path = output_dir / info.file_name
        assert path.is_file() and path.resolve().parent == output_dir.resolve()
        assert path.stat().st_size == int(info.size)


@pytest.mark.parametrize("case", case_parameters("music_save_as_file"))
def test_save_as_file(case, request, integration_profile, low_level_profile, online_output_dir):
    kwargs, capability = _case_kwargs(case, request, integration_profile, low_level_profile)
    fmt = case["expected_return_contract"]["format"]
    assert kwargs["data_format"] == fmt
    assert fmt in capability["formats"]
    path = Path(kwargs["file_name"])
    assert path.resolve().parent == online_output_dir.resolve()
    assert not path.exists()
    assert "dataFormat" not in kwargs["params"]
    assert "savepath" not in kwargs["params"]

    result = request.getfixturevalue("real_client").callAPI_to_saveAsFile(**kwargs)

    assert isinstance(result, FilesInfo)
    assert result.ok, f"{case['case_id']}: {result.request.error_code} {result.request.error_message}"
    assert case["expected_return_contract"]["kind"] == "FilesInfo"
    assert kwargs["params"]["dataFormat"] == fmt
    assert kwargs["params"]["savepath"] == str(path)
    assert len(result.files_info) == 1
    info, = result.files_info
    assert isinstance(info, FileInfo)
    assert info.file_name == path.name
    assert info.size.isdecimal()
    assert path.is_file()
    size = path.stat().st_size
    assert 0 < size == int(info.size) <= min(
        capability["max_output_bytes"], case["expected_return_contract"]["max_bytes"]
    )
    assert {item.name for item in online_output_dir.iterdir()} == {path.name}

    content = path.read_text(encoding="utf-8")
    cycle_time = kwargs["params"]["time"]
    if fmt == "json":
        payload = json.loads(content)
        assert str(payload["returnCode"]) == "0"
        assert payload["DS"][0]["datetime"] == cycle_time
        assert "TEM_103" in payload["DS"][0]
    elif fmt == "xml":
        root = ET.fromstring(content)
        assert root.attrib["returnCode"] == "0"
        record = root.find("R")
        assert record is not None and record.attrib["datetime"] == cycle_time
        assert "TEM_103" in record.attrib
    elif fmt == "text":
        assert "TEM_103" in content
        assert cycle_time in content
        assert content.count("\n") >= 2
    elif fmt == "html":
        assert content.startswith("<table")
        assert "<tbody>" in content and "</table>" in content
        assert cycle_time in content
    else:
        pytest.fail(f"Unexpected format in B13 case: {fmt}")
