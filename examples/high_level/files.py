"""Offline surface-file downloads shared with the executable guide.

From the repository root: ``python -m examples.high_level.files``.
Tiny synthetic files are streamed to a temporary directory and then removed.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_files_info_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.music import CMADaaSError
from nuwe_cmadaas.obs import download_obs_file


def make_file_client():
    """Register exact file lists and download bodies, including empty/error lists."""
    transport = SyntheticTransport()

    def register(interface_id, params, files):
        infos = []
        for name, content in files:
            url = f"https://synthetic.invalid/{name}"
            infos.append({"file_name": name, "file_url": url, "size": str(len(content))})
            transport.register_download(url, content)
        transport.register_api(
            "callAPI_to_fileList", interface_id, params,
            make_files_info_content(file_infos=infos),
        )

    register(
        "getSurfFileByTime",
        {"dataCode": "SYNTHETIC_FILES", "times": "20260102000000", "limitCnt": 1},
        [("synthetic.bin", b"FAKE")],
    )
    register(
        "getSurfFileByTimeRange",
        {"dataCode": "SYNTHETIC_FILES", "timeRange": "[20260102000000,20260102010000)",
         "limitCnt": 2},
        [("range-a.bin", b"RANGE-A"), ("range-b.bin", b"RANGE-B")],
    )
    register(
        "getSurfFileByTimeRangeAndStaID",
        {"dataCode": "SYNTHETIC_FILES", "timeRange": "[20260102000000,20260102010000)",
         "staIds": "FAKE001", "limitCnt": 1},
        [("station.bin", b"STATION")],
    )
    register(
        "getSurfFileByTime",
        {"dataCode": "SYNTHETIC_EMPTY", "times": "20260102000000", "limitCnt": 1}, [],
    )
    transport.register_api(
        "callAPI_to_fileList", "getSurfFileByTime",
        {"dataCode": "SYNTHETIC_ERROR", "times": "20260102000000", "limitCnt": 1},
        make_files_info_content(
            file_infos=[], error_code=-1234, error_message="Synthetic file-list failure",
        ),
    )
    return make_synthetic_music_client(transport), transport


def check_results(results, output_root, transport, failed_code):
    """Check paths against disk content, not just the returned file names."""
    output_root = Path(output_root)
    expected = {
        "single": [("synthetic.bin", b"FAKE")],
        "range": [("range-a.bin", b"RANGE-A"), ("range-b.bin", b"RANGE-B")],
        "station": [("station.bin", b"STATION")],
    }
    assert set(results) == {*expected, "empty"}
    for group, files in expected.items():
        paths = results[group]
        assert isinstance(paths, list)
        assert len(paths) == len(files)
        for path, (name, content) in zip(paths, files):
            assert isinstance(path, Path)
            assert path == output_root / group / name
            assert path.is_file()
            assert path.resolve().parent == (output_root / group).resolve()
            assert path.stat().st_size == len(content)
            assert path.read_bytes() == content
    assert results["empty"] == []
    assert failed_code == -1234
    assert not (output_root / "empty").exists()
    assert not (output_root / "error").exists()
    assert not (output_root / "rejected").exists()
    assert sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*")
                  if path.is_file()) == [
        "range/range-a.bin", "range/range-b.bin", "single/synthetic.bin", "station/station.bin",
    ]
    assert len(transport.calls) == 9
    assert len(transport.responses) == 9
    assert sum(response.streamed for response in transport.responses) == 4
    assert all(response.closed for response in transport.responses)


def run_example():
    """Return deterministic summaries after verifying and cleaning all files."""
    client, transport = make_file_client()
    time = pd.Timestamp("2026-01-02")
    interval = pd.Interval(time, time + pd.Timedelta(hours=1), closed="left")
    with TemporaryDirectory() as directory:
        output_root = Path(directory)
        results = {}
        for group, selectors in [
            ("single", {"time": time, "count": 1}),
            ("range", {"time": interval, "count": 2}),
            ("station", {"time": interval, "station": "FAKE001", "count": 1}),
        ]:
            results[group] = download_obs_file(
                "SYNTHETIC_FILES", output_dir=output_root / group,
                client=client, strict=True, **selectors,
            )
        results["empty"] = download_obs_file(
            "SYNTHETIC_EMPTY", time=time, count=1, output_dir=output_root / "empty",
            client=client, strict=True,
        )
        failed_code = None
        try:
            download_obs_file(
                "SYNTHETIC_ERROR", time=time, count=1, output_dir=output_root / "error",
                client=client, strict=True,
            )
        except CMADaaSError as error:
            failed_code = error.error_code
            assert error.interface_id == "getSurfFileByTime"
        else:
            raise AssertionError("failed file list must raise in strict mode")
        for selectors, error_type in [
            ({"time": pd.Timedelta(hours=6)}, UnsupportedQueryError),
            ({"time": time, "station": "FAKE001"}, UnsupportedQueryError),
            ({"time": time, "count": 0}, ValueError),
        ]:
            calls_before = len(transport.calls)
            try:
                download_obs_file(
                    "SYNTHETIC_FILES", output_dir=output_root / "rejected",
                    client=client, strict=True, **selectors,
                )
            except error_type:
                assert len(transport.calls) == calls_before
            else:
                raise AssertionError(f"invalid selectors must fail before a request: {selectors}")
        check_results(results, output_root, transport, failed_code)
        summaries = [
            (path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
            for paths in results.values() for path in paths
        ]
    assert not output_root.exists()
    return summaries


if __name__ == "__main__":
    for relative_name, size, content in run_example():
        print(f"{relative_name}: {size} bytes, {content!r}")
    print("Empty list and synthetic service error checked; temporary files removed.")
    print("All synthetic surface-file contracts passed.")
