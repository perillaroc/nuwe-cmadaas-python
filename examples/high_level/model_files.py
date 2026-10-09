"""Offline model-file downloads and latest-time tables shared with the guide.

From the repository root: ``python -m examples.high_level.model_files``.
Tiny synthetic files are streamed to a temporary directory and then removed.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_files_info_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.model import download_model_file
from nuwe_cmadaas.music import CMADaaSError


def make_model_file_client():
    """Register exact lists, download bodies, empty/errors and a latest-time table."""
    transport = SyntheticTransport()
    base = {"dataCode": "SYNTHETIC_MODEL_FILES"}
    time = {"time": "20260102060000"}
    window = {"timeRange": "[20260102060000,20260102070000)"}
    element = {"fcstEle": "synthetic_temperature", "levelType": "103"}

    def register(interface_id, selectors, name, content):
        url = f"https://synthetic.invalid/{name}"
        transport.register_download(url, content)
        transport.register_api(
            "callAPI_to_fileList", interface_id, {**base, **selectors},
            make_files_info_content(file_infos=[{
                "file_name": name, "file_url": url, "size": str(len(content)),
            }]),
        )

    register("getNafpFileByTime", {**time, "limitCnt": "1"}, "time.bin", b"TIME")
    register("getNafpFileByTimeRange", {**window, "limitCnt": "1"}, "range.bin", b"RANGE")
    register("getNafpFileByElementAndTime", {**time, **element}, "element.bin", b"ELEMENT")
    register(
        "getNafpFileByElementAndTimeRange", {**window, **element},
        "element-range.bin", b"ELEMENT-RANGE",
    )
    register(
        "getNafpFileByElementAndTimeAndLevel", {**time, **element, "fcstLevel": "2"},
        "level.bin", b"LEVEL",
    )
    register(
        "getNafpFileByElementAndTimeAndValidtime", {**time, **element, "validTime": "24"},
        "lead.bin", b"LEAD",
    )
    register(
        "getNafpFileByElementAndTimeAndLevelAndValidtime",
        {**time, **element, "fcstLevel": "2", "validTime": "24"},
        "level-lead.bin", b"LEVEL-LEAD",
    )
    register(
        "getNafpFileByTime", {**time, "limitCnt": "1", "eleValueRanges": "Validtime_C:'024'"},
        "filtered.bin", b"FILTERED",
    )
    for code, error_code in [("SYNTHETIC_EMPTY", 0), ("SYNTHETIC_ERROR", -5234)]:
        transport.register_api(
            "callAPI_to_fileList", "getNafpFileByTime",
            {"dataCode": code, **time, "limitCnt": "1"},
            make_files_info_content(
                file_infos=[], error_code=error_code,
                error_message="Synthetic model-file failure" if error_code else "",
            ),
        )
    transport.register_api(
        "callAPI_to_array2D", "getNafpLatestTime", {**base, "latestTime": "72"},
        make_array2d_content(rows=[["20260102060000"]], element_names=["Datetime"]),
    )
    return make_synthetic_music_client(transport), transport


def check_results(results, latest, output_root, transport, failed_code):
    """Check actual disk paths/content, latest table, request count and cleanup boundaries."""
    output_root = Path(output_root)
    expected = {
        "single": ("time.bin", b"TIME"), "range": ("range.bin", b"RANGE"),
        "element": ("element.bin", b"ELEMENT"),
        "element_range": ("element-range.bin", b"ELEMENT-RANGE"),
        "level": ("level.bin", b"LEVEL"), "lead": ("lead.bin", b"LEAD"),
        "level_lead": ("level-lead.bin", b"LEVEL-LEAD"),
        "filtered": ("filtered.bin", b"FILTERED"),
    }
    assert set(results) == {*expected, "empty"}
    for group, (name, content) in expected.items():
        paths = results[group]
        assert isinstance(paths, list) and len(paths) == 1
        path = paths[0]
        assert isinstance(path, Path)
        assert path == output_root / group / name
        assert path.resolve().parent == (output_root / group).resolve()
        assert path.is_file() and path.stat().st_size == len(content)
        assert path.read_bytes() == content
    assert sorted(path.relative_to(output_root).as_posix() for path in output_root.rglob("*")
                  if path.is_file()) == sorted(f"{group}/{name}" for group, (name, _) in expected.items())
    assert results["empty"] == []
    for group in ["empty", "error", "rejected"]:
        assert not (output_root / group).exists()
    assert failed_code == -5234
    assert isinstance(latest, pd.DataFrame)
    assert latest.columns.tolist() == ["Datetime"]
    assert latest.values.tolist() == [["20260102060000"]]
    assert latest.attrs == {
        "interface_id": "getNafpLatestTime", "request_time": "20260102000000",
        "response_time": "20260102000001",
    }
    assert len(transport.calls) == len(transport.responses) == 19
    assert sum(response.streamed for response in transport.responses) == 8
    assert all(response.closed for response in transport.responses)


def run_example():
    """Execute public downloads, latest table and local errors; return cleaned summaries."""
    client, transport = make_model_file_client()
    cycle = pd.Timestamp("2026-01-02 06:00")
    window = pd.Interval(cycle, cycle + pd.Timedelta(hours=1), closed="left")
    element = {"parameter": "synthetic_temperature", "level_type": 103}
    with TemporaryDirectory() as directory:
        output_root = Path(directory)
        results = {}
        for group, selectors in [
            ("single", {"start_time": cycle, "count": 1}),
            ("range", {"start_time": window, "count": 1}),
            ("element", {"start_time": cycle, **element}),
            ("element_range", {"start_time": window, **element}),
            ("level", {"start_time": cycle, **element, "level": 2}),
            ("lead", {"start_time": cycle, **element, "forecast_time": "24h"}),
            ("level_lead", {"start_time": cycle, **element, "level": 2, "forecast_time": "24h"}),
            ("filtered", {"start_time": cycle, "forecast_time": "24h", "count": 1,
                          "data_type": "analysis"}),
        ]:
            results[group] = download_model_file(
                "SYNTHETIC_MODEL_FILES", output_dir=output_root / group,
                client=client, strict=True, **selectors,
            )
        response = client.callAPI_to_array2D(
            "getNafpLatestTime", {"dataCode": "SYNTHETIC_MODEL_FILES", "latestTime": "72"},
        )
        response.raise_for_error(interface_id="getNafpLatestTime")
        latest = response.to_pandas()
        results["empty"] = download_model_file(
            "SYNTHETIC_EMPTY", start_time=cycle, count=1, output_dir=output_root / "empty",
            client=client, strict=True,
        )
        failed_code = None
        try:
            download_model_file(
                "SYNTHETIC_ERROR", start_time=cycle, count=1, output_dir=output_root / "error",
                client=client, strict=True,
            )
        except CMADaaSError as error:
            failed_code = error.error_code
            assert error.interface_id == "getNafpFileByTime"
        else:
            raise AssertionError("failed file list must raise in strict mode")
        for selectors, error_type in [
            ({"start_time": pd.Timedelta(hours=72)}, UnsupportedQueryError),
            ({}, UnsupportedQueryError),
            ({"start_time": cycle, "parameter": "synthetic_temperature"}, ValueError),
            ({"start_time": cycle, **element, "count": 1}, ValueError),
            ({"start_time": cycle, "count": 0}, ValueError),
            ({"start_time": window, **element, "level": 2}, UnsupportedQueryError),
            ({"start_time": cycle, "forecast_time": ("6h", "24h")}, TypeError),
            ({"start_time": [cycle]}, ValueError),
            ({"start_time": cycle, "region": {
                "type": "rect", "start_longitude": 110, "end_longitude": 111,
                "start_latitude": 30, "end_latitude": 31,
            }}, UnsupportedQueryError),
        ]:
            calls_before = len(transport.calls)
            try:
                download_model_file(
                    "SYNTHETIC_MODEL_FILES", output_dir=output_root / "rejected",
                    client=client, strict=True, **selectors,
                )
            except error_type:
                assert len(transport.calls) == calls_before
            else:
                raise AssertionError(f"invalid selectors must fail before a request: {selectors}")
        check_results(results, latest, output_root, transport, failed_code)
        summaries = [(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
                     for paths in results.values() for path in paths]
    assert not output_root.exists()
    return summaries, latest


if __name__ == "__main__":
    summaries, latest = run_example()
    for relative_name, size, content in summaries:
        print(f"{relative_name}: {size} bytes, {content!r}")
    print(f"Latest-time table (not a download):\n{latest}")
    print("All synthetic model-file contracts passed; temporary files removed.")
