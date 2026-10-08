"""Bounded, service-backed downloads from cataloged surface file interfaces."""

import pytest

from nuwe_cmadaas.obs import download_obs_file
from tests.integration.case_registry import case_parameters, resolve_case_value
from tests.integration.file_download import BoundedDownloadClient, assert_downloaded_files


@pytest.mark.parametrize("case", case_parameters("obs_file"))
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    limits = integration_profile.get("download_limits", {})
    if limits.get("preflight_file_list") is not True:
        pytest.skip("File-list preflight is required for surface file cases")
    max_files = limits["max_files"]
    max_total_bytes = limits["max_total_bytes"]
    assert type(max_files) is int and max_files > 0
    assert type(max_total_bytes) is int and max_total_bytes > 0
    assert type(dataset["max_files"]) is int and 0 < dataset["max_files"] <= max_files

    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    client = BoundedDownloadClient(
        request.getfixturevalue("real_client"),
        max_files=max_files,
        max_total_bytes=max_total_bytes,
    )
    paths = download_obs_file(**kwargs, client=client, strict=True)

    expected = case["expected_return_contract"]
    assert expected["kind"] == "paths"
    assert_downloaded_files(
        paths, kwargs["output_dir"], client,
        max_files=max_files, max_total_bytes=max_total_bytes,
    )
