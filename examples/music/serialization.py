"""Native formatted strings and saved files shared with executable guides.

From the repository root: ``python -m examples.music.serialization``.
All response text, protobuf metadata and downloaded bodies are synthetic.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

from examples._support import SyntheticTransport, make_files_info_content, make_synthetic_music_client
from nuwe_cmadaas.music import CMADaaSError, FilesInfo


def make_formatted_content(fmt):
    """Build one fictional point record in each demonstrated service format."""
    row = {
        "lat": "30.0", "lon": "110.0", "datetime": "20260102060000",
        "level": "2", "validtime": "24", "synthetic_temperature_103": "280.0",
    }
    if fmt == "json":
        return json.dumps({"returnCode": "0", "DS": [row]})
    if fmt == "xml":
        root = ET.Element("Response", returnCode="0")
        ET.SubElement(root, "R", row)
        return ET.tostring(root, encoding="unicode")
    if fmt == "text":
        return 'returnCode="0"\n' + " ".join(row) + "\n" + " ".join(row.values()) + "\n"
    if fmt == "html":
        return (
            "<table><thead><tr>" + "".join(f"<th>{name}</th>" for name in row)
            + "</tr></thead><tbody><tr>" + "".join(f"<td>{value}</td>" for value in row.values())
            + "</tr></tbody></table>"
        )
    raise ValueError(f"unsupported synthetic format: {fmt}")


def _base_params(code):
    return {
        "dataCode": code, "fcstEle": "synthetic_temperature", "time": "20260102060000",
        "levelType": "103", "fcstLevel": "2", "validTime": "24", "latLons": "30.0/110.0",
    }


def make_serialization_client():
    """Register formatted strings, a gateway error, raw business error and bad UTF-8."""
    transport = SyntheticTransport()
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    for fmt in ["json", "xml", "text", "html"]:
        transport.register_api(
            "callAPI_to_serializedStr", interface_id,
            {**_base_params("SYNTHETIC_SERIALIZED"), "dataFormat": fmt},
            make_formatted_content(fmt).encode("utf-8"),
        )
    for code, content in [
        ("SYNTHETIC_GATEWAY", b'{"flag":"slb","returnCode":-9234,"returnMessage":"Synthetic gateway failure"}'),
        ("SYNTHETIC_ERROR", b'{"returnCode":-9235,"returnMessage":"Synthetic formatted service failure","DS":[]}'),
        ("SYNTHETIC_UTF8", b"\xff"),
    ]:
        transport.register_api(
            "callAPI_to_serializedStr", interface_id,
            {**_base_params(code), "dataFormat": "json"}, content,
        )
    return make_synthetic_music_client(transport), transport


def make_save_client(output_root):
    """Register exact savepath queries; do not prewrite any local file."""
    root = Path(output_root)
    transport = SyntheticTransport()
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    for fmt in ["json", "xml", "text", "html"]:
        body = make_formatted_content(fmt).encode("utf-8")
        url = f"https://synthetic.invalid/save/{fmt}"
        transport.register_download(url, body)
        transport.register_api(
            "callAPI_to_saveAsFile", interface_id,
            {**_base_params("SYNTHETIC_SAVE"), "dataFormat": fmt, "savepath": str(root / f"point.{fmt}")},
            make_files_info_content(file_infos=[{
                "file_name": f"service-result.{fmt}", "suffix": fmt, "size": str(len(body)),
                "save_path": f"/synthetic/service/result.{fmt}", "file_url": url,
            }]),
        )
    for code, filename, content in [
        ("SYNTHETIC_ERROR", "failed.json", make_files_info_content(
            file_infos=[], error_code=-9236, error_message="Synthetic save service failure",
        )),
        ("SYNTHETIC_GATEWAY", "gateway.json",
         b'{"flag":"slb","returnCode":-9234,"returnMessage":"Synthetic gateway failure"}'),
        ("SYNTHETIC_DECODE", "decode.json", b"\xff"),
        ("SYNTHETIC_EMPTY", "empty.json", make_files_info_content(file_infos=[])),
    ]:
        transport.register_api(
            "callAPI_to_saveAsFile", interface_id,
            {**_base_params(code), "dataFormat": "json", "savepath": str(root / filename)}, content,
        )
    return make_synthetic_music_client(transport), transport


def check_formatted_content(content, fmt):
    """Parse and compare independent expected fields and string values."""
    expected = {
        "lat": "30.0", "lon": "110.0", "datetime": "20260102060000",
        "level": "2", "validtime": "24", "synthetic_temperature_103": "280.0",
    }
    assert isinstance(content, str) and len(content.encode("utf-8")) < 1024
    if fmt == "json":
        payload = json.loads(content)
        assert payload["returnCode"] == "0" and payload["DS"] == [expected]
    elif fmt == "xml":
        root = ET.fromstring(content)
        assert root.attrib == {"returnCode": "0"}
        assert len(root) == 1 and root[0].tag == "R" and root[0].attrib == expected
    elif fmt == "text":
        lines = content.splitlines()
        assert lines[0] == 'returnCode="0"' and len(lines) == 3
        assert lines[1].split() == list(expected) and lines[2].split() == list(expected.values())
    elif fmt == "html":
        root = ET.fromstring(content)
        assert root.tag == "table"
        assert [cell.text for cell in root.findall("thead/tr/th")] == list(expected)
        assert [cell.text for cell in root.findall("tbody/tr/td")] == list(expected.values())
    else:
        raise AssertionError("unexpected result format")


def check_serialization_results(contents, queries, preserved, errors, output_root, transport):
    """Verify string formats, mutation, compatible errors and absence of disk writes."""
    assert set(contents) == set(queries) == {"json", "xml", "text", "html"}
    for fmt, content in contents.items():
        check_formatted_content(content, fmt)
        assert queries[fmt] == {**_base_params("SYNTHETIC_SERIALIZED"), "dataFormat": fmt}
        assert not hasattr(content, "ok") and not hasattr(content, "request")
    assert preserved == {**_base_params("SYNTHETIC_SERIALIZED"), "dataFormat": "json"}
    assert errors["gateway"] == "getway error: returnCode=-9234 returnMessage=Synthetic gateway failure"
    assert json.loads(errors["business"])["returnCode"] == -9235
    assert errors["utf8"] == "UnicodeDecodeError"
    assert list(Path(output_root).iterdir()) == []
    assert len(transport.calls) == len(transport.responses) == 8
    assert all(response.closed and not response.streamed for response in transport.responses)


def check_save_results(results, queries, preserved, failures, output_root, transport):
    """Verify actual bytes, metadata, parameter updates and no output on failure."""
    root = Path(output_root)
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    assert set(results) == set(queries) == {"json", "xml", "text", "html"}
    for fmt, response in results.items():
        path = root / f"point.{fmt}"
        assert isinstance(response, FilesInfo) and response.ok
        assert response.raise_for_error(interface_id=interface_id, params=queries[fmt]) is response
        assert queries[fmt] == {
            **_base_params("SYNTHETIC_SAVE"), "dataFormat": fmt, "savepath": str(path),
        }
        assert path.is_file() and path.resolve().parent == root.resolve()
        check_formatted_content(path.read_text(encoding="utf-8"), fmt)
        info, = response.files_info
        assert info.file_name == f"service-result.{fmt}" and info.suffix == fmt
        assert info.save_path == f"/synthetic/service/result.{fmt}"
        assert info.file_url == f"https://synthetic.invalid/save/{fmt}"
        assert int(info.size) == path.stat().st_size
        assert response.metadata == {
            "interface_id": interface_id, "time": "20260102060000", "valid_time": "24",
            "level_type": "103", "level": "2",
        }
    assert preserved == {**_base_params("SYNTHETIC_SAVE"), "dataFormat": "json", "savepath": str(root / "point.json")}
    assert set(failures) == {"service", "gateway", "decode", "none", "empty"}
    for name, code in [("service", -9236), ("gateway", -9234), ("decode", -10003), ("none", -10001)]:
        response = failures[name]
        assert isinstance(response, FilesInfo) and not response.ok
        assert response.request.error_code == code
        try:
            response.raise_for_error(interface_id=interface_id)
        except CMADaaSError as error:
            assert error.error_code == code and error.interface_id == interface_id
        else:
            raise AssertionError("failed save response must raise")
    assert failures["empty"] == "IndexError"
    assert {path.name for path in root.iterdir()} == {"point.json", "point.xml", "point.text", "point.html"}
    assert not list(root.rglob("*.part"))
    assert len(transport.calls) == len(transport.responses) == 14
    assert sum(response.streamed for response in transport.responses) == 5
    assert all(response.closed for response in transport.responses)


def run_serialization_example():
    client, transport = make_serialization_client()
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    with TemporaryDirectory() as directory:
        contents, queries = {}, {}
        for fmt in ["json", "xml", "text", "html"]:
            queries[fmt] = _base_params("SYNTHETIC_SERIALIZED")
            contents[fmt] = client.callAPI_to_serializedStr(interface_id, queries[fmt], fmt)
        preserved = {**_base_params("SYNTHETIC_SERIALIZED"), "dataFormat": "json"}
        assert client.callAPI_to_serializedStr(interface_id, preserved, "xml") == contents["json"]
        errors = {}
        for name, code in [("gateway", "SYNTHETIC_GATEWAY"), ("business", "SYNTHETIC_ERROR")]:
            errors[name] = client.callAPI_to_serializedStr(interface_id, _base_params(code), "json")
        try:
            client.callAPI_to_serializedStr(interface_id, _base_params("SYNTHETIC_UTF8"), "json")
        except UnicodeDecodeError as error:
            errors["utf8"] = type(error).__name__
        else:
            raise AssertionError("invalid UTF-8 must propagate")
        check_serialization_results(contents, queries, preserved, errors, directory, transport)
    assert not Path(directory).exists()
    return contents, errors


def run_save_example():
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
    with TemporaryDirectory() as directory:
        root = Path(directory)
        client, transport = make_save_client(root)
        results, queries = {}, {}
        for fmt in ["json", "xml", "text", "html"]:
            queries[fmt] = _base_params("SYNTHETIC_SAVE")
            results[fmt] = client.callAPI_to_saveAsFile(interface_id, queries[fmt], fmt, str(root / f"point.{fmt}"))
            results[fmt].raise_for_error(interface_id=interface_id, params=queries[fmt])
        (root / "point.json").write_bytes(b"LOCAL")
        preserved = {**_base_params("SYNTHETIC_SAVE"), "dataFormat": "json", "savepath": "old-path"}
        repeated = client.callAPI_to_saveAsFile(interface_id, preserved, "xml", str(root / "point.json"))
        repeated.raise_for_error(interface_id=interface_id, params=preserved)
        failures = {}
        for name, code, filename in [
            ("service", "SYNTHETIC_ERROR", "failed.json"),
            ("gateway", "SYNTHETIC_GATEWAY", "gateway.json"),
            ("decode", "SYNTHETIC_DECODE", "decode.json"),
        ]:
            query = _base_params(code)
            failures[name] = client.callAPI_to_saveAsFile(interface_id, query, "json", str(root / filename))
            assert query["dataFormat"] == "json" and query["savepath"] == str(root / filename)
        none_params = _base_params("SYNTHETIC_SAVE")
        before = len(transport.calls)
        failures["none"] = client.callAPI_to_saveAsFile(interface_id, none_params, "json", None)
        assert len(transport.calls) == before
        assert none_params == {**_base_params("SYNTHETIC_SAVE"), "dataFormat": "json"}
        try:
            client.callAPI_to_saveAsFile(interface_id, _base_params("SYNTHETIC_EMPTY"), "json", str(root / "empty.json"))
        except IndexError as error:
            failures["empty"] = type(error).__name__
        else:
            raise AssertionError("current empty save list behavior must be explicit")
        check_save_results(results, queries, preserved, failures, root, transport)
        summaries = [(path.name, path.stat().st_size) for path in sorted(root.iterdir())]
    assert not root.exists()
    return summaries


if __name__ == "__main__":
    contents, errors = run_serialization_example()
    for fmt, content in contents.items():
        print(f"\n{fmt}:\n{content}")
    print("\nCompatible string errors:", errors)
    print("\nSaved and parsed files:", run_save_example())
    print("All synthetic formatted-output contracts passed; temporary files removed.")
