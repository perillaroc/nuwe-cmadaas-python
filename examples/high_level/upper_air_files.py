"""Offline upper-air-file downloads shared with the executable guide.

From the repository root: ``python -m examples.high_level.upper_air_files``.
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
from nuwe_cmadaas.obs import download_obs_upper_air_file


def make_upper_file_client():
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
        "getUparFileByTime",
        {"dataCode": "SYNTHETIC_UPPER_FILES", "times": "20260102000000", "limitCnt": 1},
        [("upper.bin", b"UPPER")],
    )
    register(
        "getUparFileByTimeRange",
        {"dataCode": "SYNTHETIC_UPPER_FILES", "timeRange": "[20260102000000,20260102010000)",
         "limitCnt": 1},
        [("range.bin", b"RANGE")],
    )
    register(
        "getUparFileByTimeAndStaID",
        {"dataCode": "SYNTHETIC_UPPER_FILES", "times": "20260102000000",
         "staIds": "FAKE001", "limitCnt": 1},
        [("station.bin", b"STATION")],
    )
    register(
        "getUparFileByTimeRangeAndStaID",
        {"dataCode": "SYNTHETIC_UPPER_FILES", "timeRange": "[20260102000000,20260102010000)",
         "staIds": "FAKE001,FAKE002", "limitCnt": 1},
        [("window.bin", b"WINDOW")],
    )
    register(
        "getUparFileByTime",
        {"dataCode": "SYNTHETIC_EMPTY", "times": "20260102000000", "limitCnt": 1}, [],
    )
    transport.register_api(
        "callAPI_to_fileList", "getUparFileByTime",
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
        "single": [("upper.bin", b"UPPER")],
        "range": [("range.bin", b"RANGE")],
        "station": [("station.bin", b"STATION")],
        "station_range": [("window.bin", b"WINDOW")],
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
        "range/range.bin", "single/upper.bin", "station/station.bin", "station_range/window.bin",
    ]
    assert len(transport.calls) == 10
    assert len(transport.responses) == 10
    assert sum(response.streamed for response in transport.responses) == 4
    assert all(response.closed for response in transport.responses)


def run_example():
    """Return deterministic summaries after verifying and cleaning all files."""
    client, transport = make_upper_file_client()
    time = pd.Timestamp("2026-01-02")
    interval = pd.Interval(time, time + pd.Timedelta(hours=1), closed="left")
    with TemporaryDirectory() as directory:
        output_root = Path(directory)
        results = {}
        for group, selectors in [
            ("single", {"time": time, "count": 1}),
            ("range", {"time": interval, "count": 1}),
            ("station", {"time": time, "station": "FAKE001", "count": 1}),
            ("station_range", {"time": interval, "station": ["FAKE001", "FAKE002"], "count": 1}),
        ]:
            results[group] = download_obs_upper_air_file(
                "SYNTHETIC_UPPER_FILES", output_dir=output_root / group,
                client=client, strict=True, **selectors,
            )
        results["empty"] = download_obs_upper_air_file(
            "SYNTHETIC_EMPTY", time=time, count=1, output_dir=output_root / "empty",
            client=client, strict=True,
        )
        failed_code = None
        try:
            download_obs_upper_air_file(
                "SYNTHETIC_ERROR", time=time, count=1, output_dir=output_root / "error",
                client=client, strict=True,
            )
        except CMADaaSError as error:
            failed_code = error.error_code
            assert error.interface_id == "getUparFileByTime"
        else:
            raise AssertionError("failed file list must raise in strict mode")
        for selectors, error_type in [
            ({"time": pd.Timedelta(hours=6)}, UnsupportedQueryError),
            ({}, UnsupportedQueryError),
            ({"time": time, "station": ("FAKE001", "FAKE002")}, UnsupportedQueryError),
            ({"time": time, "count": 0}, ValueError),
        ]:
            calls_before = len(transport.calls)
            try:
                download_obs_upper_air_file(
                    "SYNTHETIC_UPPER_FILES", output_dir=output_root / "rejected",
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
    print("All synthetic upper-air-file contracts passed.")
