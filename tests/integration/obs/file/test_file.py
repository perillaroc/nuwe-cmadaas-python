"""Bounded, service-backed downloads from cataloged surface file interfaces."""

from pathlib import Path

import pytest

from nuwe_cmadaas.obs import download_obs_file
from tests.integration.case_registry import case_parameters, resolve_case_value


class BoundedDownloadClient:
    """Check the exact file query before allowing the high-level download call."""

    def __init__(self, client, *, max_files, max_total_bytes):
        self.client = client
        self.max_files = max_files
        self.max_total_bytes = max_total_bytes
        self.preflight_names = None

    def callAPI_to_downFile(self, interface_id, params, file_dir):
        listing = self.client.callAPI_to_fileList(interface_id, params.copy())
        assert listing.ok, (
            f"File preflight failed for {interface_id}: "
            f"{listing.request.error_code} {listing.request.error_message}"
        )
        files = listing.files_info
        assert 0 < len(files) <= self.max_files, (
            f"File preflight returned {len(files)} files; limit is {self.max_files}"
        )
        names = [info.file_name for info in files]
        assert all(
            name and name not in {".", ".."} and Path(name).name == name
            and "\\" not in name for name in names
        ), "File preflight contains unsafe names"
        assert len(names) == len(set(names)), "File preflight contains duplicate names"
        assert all(info.file_url for info in files), "File preflight lacks download URLs"
        sizes = [info.size for info in files]
        assert all(size.isdecimal() for size in sizes), "File size must be known in bytes"
        assert sum(int(size) for size in sizes) <= self.max_total_bytes, (
            f"File preflight exceeds {self.max_total_bytes} bytes"
        )
        self.preflight_names = set(names)
        return self.client.callAPI_to_downFile(interface_id, params, file_dir=file_dir)


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
    assert isinstance(paths, list)
    assert paths
    output_dir = Path(kwargs["output_dir"]).resolve()
    assert len(paths) <= max_files
    assert {path.name for path in paths} == client.preflight_names
    assert all(isinstance(path, Path) for path in paths)
    assert all(path.resolve().parent == output_dir for path in paths)
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
    assert sum(path.stat().st_size for path in paths) <= max_total_bytes
