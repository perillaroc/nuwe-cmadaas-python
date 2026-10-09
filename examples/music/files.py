"""Native file-list and download workflows shared with executable guides.

From the repository root: ``python -m examples.music.files``.
Small synthetic files are streamed, verified and removed with temporary folders.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from examples._support import (
    SyntheticTransport,
    make_files_info_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.music import CMADaaSDownloadError, CMADaaSRequestError, FileInfo, FilesInfo


def make_file_client():
    """Register native listings and two tiny bodies, including empty/error lists."""
    transport = SyntheticTransport()
    interface_id = "getNafpFileByElementAndTime"
    params = {
        "dataCode": "SYNTHETIC_FILES", "fcstEle": "synthetic_temperature",
        "levelType": "103", "time": "20260102060000",
    }
    infos = []
    for name, content in [("first.bin", b"FAKE"), ("second.bin", b"SECOND")]:
        url = f"https://synthetic.invalid/{name}"
        infos.append({
            "file_name": name, "save_path": f"/synthetic/service/{name}",
            "suffix": "bin", "size": str(len(content)), "file_url": url,
            "image_base64": "", "attributes": ["synthetic", "offline"],
        })
        transport.register_download(url, content)
    for code, files, error_code in [
        ("SYNTHETIC_FILES", infos, 0), ("SYNTHETIC_EMPTY", [], 0),
        ("SYNTHETIC_ERROR", [], -8234),
    ]:
        transport.register_api(
            "callAPI_to_fileList", interface_id, {**params, "dataCode": code},
            make_files_info_content(
                file_infos=files, error_code=error_code,
                error_message="Synthetic file-list service failure" if error_code else "",
            ),
        )
    return make_synthetic_music_client(transport), transport


def _check_listing(response, params, expected_files, error_code=0):
    """Check response fields independently of the synthetic factory."""
    interface_id = "getNafpFileByElementAndTime"
    assert isinstance(response, FilesInfo)
    assert response.ok is (error_code == 0)
    assert response.request.error_code == error_code
    assert response.metadata == {
        "interface_id": interface_id, "time": "20260102060000", "level_type": "103",
    }
    assert response.request.request_time == "20260102000000"
    assert response.request.response_time == "20260102000001"
    assert len(response.files_info) == len(expected_files)
    for info, (name, content) in zip(response.files_info, expected_files):
        assert isinstance(info, FileInfo)
        assert info.file_name == name and info.size == str(len(content))
        assert isinstance(info.size, str) and info.suffix == "bin"
        assert info.file_url == f"https://synthetic.invalid/{name}"
        assert info.save_path == f"/synthetic/service/{name}"
        assert info.image_base64 == "" and info.attributes == ["synthetic", "offline"]
    if error_code:
        error_type = CMADaaSDownloadError if error_code == -10004 else CMADaaSRequestError
        try:
            response.raise_for_error(interface_id=interface_id, params=params)
        except error_type as error:
            assert error.error_code == error_code and error.interface_id == interface_id
            assert error.params == params
        else:
            raise AssertionError("failed response must raise with query context")
    else:
        assert response.raise_for_error(interface_id=interface_id, params=params) is response


def _check_params(params):
    assert params == {
        "dataCode": "SYNTHETIC_FILES", "fcstEle": "synthetic_temperature",
        "levelType": "103", "time": "20260102060000",
    }


def check_listing_results(responses, output_root, transport, params):
    """Verify metadata-only results, no disk writes and no binary transfers."""
    _check_params(params)
    assert set(responses) == {"listing", "empty", "failed"}
    _check_listing(responses["listing"], params, [("first.bin", b"FAKE"), ("second.bin", b"SECOND")])
    _check_listing(responses["empty"], {**params, "dataCode": "SYNTHETIC_EMPTY"}, [])
    _check_listing(responses["failed"], {**params, "dataCode": "SYNTHETIC_ERROR"}, [], -8234)
    assert responses["listing"].request.row_count == 2
    assert responses["listing"].request.col_count == 1
    assert list(Path(output_root).iterdir()) == []
    assert len(transport.calls) == len(transport.responses) == 3
    assert all(response.closed and not response.streamed for response in transport.responses)


def check_download_results(responses, output_root, transport, params):
    """Verify FilesInfo and actual disk contents after overwrite/partial failures."""
    _check_params(params)
    root = Path(output_root)
    expected_files = [("first.bin", b"FAKE"), ("second.bin", b"SECOND")]
    assert set(responses) == {"preflight", "downloaded", "protected", "overwritten", "partial", "empty", "failed"}
    for name in ["preflight", "downloaded", "overwritten"]:
        _check_listing(responses[name], params, expected_files)
    for name in ["protected", "partial"]:
        _check_listing(responses[name], params, expected_files, -10004)
        assert responses[name].request.error_message == "target file already exists"
    _check_listing(responses["empty"], {**params, "dataCode": "SYNTHETIC_EMPTY"}, [])
    _check_listing(responses["failed"], {**params, "dataCode": "SYNTHETIC_ERROR"}, [], -8234)
    expected = {
        "main/first.bin": b"FAKE", "main/second.bin": b"SECOND",
        "partial/first.bin": b"FAKE", "partial/second.bin": b"KEEP",
    }
    actual = {path.relative_to(root).as_posix(): path.read_bytes()
              for path in root.rglob("*") if path.is_file()}
    assert actual == expected
    assert not (root / "empty").exists() and not (root / "failed").exists()
    assert not list(root.rglob("*.part"))
    assert len(transport.calls) == len(transport.responses) == 12
    assert sum(response.streamed for response in transport.responses) == 5
    assert all(response.closed for response in transport.responses)
    api_calls = [url for url, _ in transport.calls if "/music-ws/api?" in url]
    assert len(api_calls) == 7
    assert all("method=callAPI_to_fileList&" in url for url in api_calls)


def run_listing_example():
    """Query three native lists and prove they do not create local files."""
    client, transport = make_file_client()
    interface_id = "getNafpFileByElementAndTime"
    params = {
        "dataCode": "SYNTHETIC_FILES", "fcstEle": "synthetic_temperature",
        "levelType": "103", "time": "20260102060000",
    }
    with TemporaryDirectory() as directory:
        responses = {}
        for name, code in [("listing", "SYNTHETIC_FILES"), ("empty", "SYNTHETIC_EMPTY"),
                           ("failed", "SYNTHETIC_ERROR")]:
            responses[name] = client.callAPI_to_fileList(interface_id, {**params, "dataCode": code})
        check_listing_results(responses, directory, transport, params)
        summary = [(info.file_name, info.size, info.suffix) for info in responses["listing"].files_info]
    assert not Path(directory).exists()
    return summary


def run_download_example():
    """Stream small files, demonstrate overwrite and partial failure, then clean up."""
    client, transport = make_file_client()
    interface_id = "getNafpFileByElementAndTime"
    params = {
        "dataCode": "SYNTHETIC_FILES", "fcstEle": "synthetic_temperature",
        "levelType": "103", "time": "20260102060000",
    }
    with TemporaryDirectory() as directory:
        root = Path(directory)
        responses = {"preflight": client.callAPI_to_fileList(interface_id, params)}
        assert list(root.iterdir()) == []
        responses["downloaded"] = client.callAPI_to_downFile(interface_id, params, root / "main", overwrite=False)
        responses["downloaded"].raise_for_error(interface_id=interface_id, params=params)
        assert (root / "main/first.bin").read_bytes() == b"FAKE"
        assert (root / "main/second.bin").read_bytes() == b"SECOND"
        calls_before = len(transport.calls)
        responses["protected"] = client.callAPI_to_downFile(interface_id, params, root / "main", overwrite=False)
        assert len(transport.calls) == calls_before + 1
        assert (root / "main/first.bin").read_bytes() == b"FAKE"
        assert (root / "main/second.bin").read_bytes() == b"SECOND"
        (root / "main/first.bin").write_bytes(b"LOCAL")
        # Omit overwrite to exercise its actual default True.
        responses["overwritten"] = client.callAPI_to_downFile(interface_id, params, root / "main")
        responses["overwritten"].raise_for_error(interface_id=interface_id, params=params)
        (root / "partial").mkdir()
        (root / "partial/second.bin").write_bytes(b"KEEP")
        calls_before = len(transport.calls)
        responses["partial"] = client.callAPI_to_downFile(interface_id, params, root / "partial", overwrite=False)
        assert len(transport.calls) == calls_before + 2
        for name, code in [("empty", "SYNTHETIC_EMPTY"), ("failed", "SYNTHETIC_ERROR")]:
            responses[name] = client.callAPI_to_downFile(
                interface_id, {**params, "dataCode": code}, root / name, overwrite=False,
            )
        check_download_results(responses, root, transport, params)
        summary = [(path.relative_to(root).as_posix(), path.stat().st_size, path.read_bytes())
                   for path in sorted(root.rglob("*.bin"))]
    assert not root.exists()
    return summary


if __name__ == "__main__":
    print("Metadata-only listing:", run_listing_example())
    for name, size, content in run_download_example():
        print(f"{name}: {size} bytes, {content!r}")
    print("Existing targets, default overwrite, partial failure and service errors checked.")
    print("All synthetic native file contracts passed; temporary files removed.")
