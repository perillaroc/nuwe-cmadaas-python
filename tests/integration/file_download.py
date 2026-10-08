"""Size checks for service-backed file download cases."""

from pathlib import Path


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


def assert_downloaded_files(paths, output_dir, client, *, max_files, max_total_bytes):
    """Verify the high-level result points to the downloaded files."""
    assert isinstance(paths, list)
    assert paths
    output_dir = Path(output_dir).resolve()
    assert len(paths) <= max_files
    assert all(isinstance(path, Path) for path in paths)
    assert {path.name for path in paths} == client.preflight_names
    assert all(path.resolve().parent == output_dir for path in paths)
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
    assert sum(path.stat().st_size for path in paths) <= max_total_bytes
