"""Opaque binary-block example shared with the executable MUSIC guide.

From the repository root: ``python -m examples.music.data_block``.
The interface, dataset, binary format and protobuf responses are fictional.
"""

from io import BytesIO
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import warnings

from examples._support import SyntheticTransport, make_data_block_content, make_synthetic_music_client
from nuwe_cmadaas.music import CMADaaSError, DataBlock


def make_data_block_client():
    """Register named non-text bytes, empty success, service failure and bad protobuf."""
    transport = SyntheticTransport()
    interface_id = "syntheticDataBlockByTime"
    body = b"NWB1" + struct.pack(">Hh", 2, -7) + b"\x00\xff"
    for code, content in [
        ("SYNTHETIC_BLOCK", make_data_block_content(data_name="synthetic_sample.bin", data=body)),
        ("SYNTHETIC_EMPTY", make_data_block_content(data_name="", data=b"")),
        ("SYNTHETIC_ERROR", make_data_block_content(
            data_name="synthetic_failed.bin", data=b"\x00\xffERROR",
            error_code=-10234, error_message="Synthetic block service failure",
        )),
        ("SYNTHETIC_DECODE", b"\xff"),
    ]:
        transport.register_api(
            "callAPI_to_dataBlock", interface_id,
            {"dataCode": code, "time": "20260102060000"}, content,
        )
    return make_synthetic_music_client(transport), transport


def read_synthetic_block(data):
    """Read the fictional ten-byte format; this is not a radar/GRIB reader."""
    if not isinstance(data, bytes) or len(data) != 10:
        raise ValueError("Expected exactly ten synthetic bytes")
    reader = BytesIO(data)
    if reader.read(4) != b"NWB1":
        raise ValueError("Unexpected synthetic format signature")
    count, signed_value = struct.unpack(">Hh", reader.read(4))
    trailer = reader.read(2)
    if trailer != b"\x00\xff" or reader.read(1) != b"":
        raise ValueError("Unexpected synthetic trailer")
    return {"count": count, "signed_value": signed_value, "trailer_hex": trailer.hex()}


def check_data_block_results(results, queries, parsed, errors, notices, output_root, transport):
    """Compare independent binary values, statuses, context and no file side effects."""
    interface_id = "syntheticDataBlockByTime"
    assert set(results) == set(queries) == {"main", "empty", "service", "decode"}
    for name, code in [
        ("main", "SYNTHETIC_BLOCK"), ("empty", "SYNTHETIC_EMPTY"),
        ("service", "SYNTHETIC_ERROR"), ("decode", "SYNTHETIC_DECODE"),
    ]:
        response = results[name]
        assert isinstance(response, DataBlock)
        assert queries[name] == {"dataCode": code, "time": "20260102060000"}
        assert response.metadata == {"interface_id": interface_id, "time": "20260102060000"}
    main = results["main"]
    assert main.ok and main.raise_for_error(interface_id=interface_id, params=queries["main"]) is main
    assert main.data_name == "synthetic_sample.bin" and isinstance(main.data_name, str)
    assert isinstance(main.data, bytes) and main.data == b"NWB1\x00\x02\xff\xf9\x00\xff"
    assert len(main.data) == 10 and main.data.hex() == "4e5742310002fff900ff"
    assert parsed == {"count": 2, "signed_value": -7, "trailer_hex": "00ff"}
    assert main.request.error_code == 0 and main.request.error_message == ""
    assert main.request.row_count == main.request.col_count == 1
    assert main.request.request_elements == "synthetic_elements"
    assert main.request.request_params == "synthetic_params"
    assert main.request.request_time == "20260102000000"
    assert main.request.response_time == "20260102000001" and main.request.take_time == 0
    assert main.request.cause is None
    assert results["empty"].ok and results["empty"].data_name == "" and results["empty"].data == b""
    assert results["service"].data_name == "synthetic_failed.bin"
    assert results["service"].data == b"\x00\xffERROR"
    assert results["service"].request.error_message == "Synthetic block service failure"
    assert results["decode"].data_name == "" and results["decode"].data == b""
    for name, code in [("service", -10234), ("decode", -10003)]:
        assert not results[name].ok and results[name].request.error_code == code
        error = errors[name]
        assert isinstance(error, CMADaaSError) and error.error_code == code
        assert error.interface_id == interface_id and error.params == queries[name]
    assert errors["utf8"] == "UnicodeDecodeError"
    assert errors["pandas"] == errors["xarray"] == "NotImplementedError"
    assert notices == ["callAPI_to_dataBlock has no verified live-service interface"] * 4
    assert list(Path(output_root).iterdir()) == []
    assert len(transport.calls) == len(transport.responses) == 4
    assert all(response.closed and not response.streamed for response in transport.responses)


def run_data_block_example():
    client, transport = make_data_block_client()
    interface_id = "syntheticDataBlockByTime"
    results, queries, errors = {}, {}, {}
    with TemporaryDirectory() as directory:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", UserWarning)
            for name, code in [
                ("main", "SYNTHETIC_BLOCK"), ("empty", "SYNTHETIC_EMPTY"),
                ("service", "SYNTHETIC_ERROR"), ("decode", "SYNTHETIC_DECODE"),
            ]:
                queries[name] = {"dataCode": code, "time": "20260102060000"}
                results[name] = client.callAPI_to_dataBlock(interface_id, queries[name])
        main = results["main"].raise_for_error(interface_id=interface_id, params=queries["main"])
        parsed = read_synthetic_block(main.data)
        for name, operation in [
            ("utf8", lambda: main.data.decode("utf-8")),
            ("pandas", main.to_pandas), ("xarray", main.to_xarray),
        ]:
            try:
                operation()
            except (UnicodeDecodeError, NotImplementedError) as error:
                errors[name] = type(error).__name__
            else:
                raise AssertionError("This block has no text/table/grid conversion")
        for name in ["service", "decode"]:
            try:
                results[name].raise_for_error(interface_id=interface_id, params=queries[name])
            except CMADaaSError as error:
                errors[name] = error
            else:
                raise AssertionError("Failed block must raise before reading")
        notices = [str(item.message) for item in caught]
        check_data_block_results(results, queries, parsed, errors, notices, directory, transport)
    assert not Path(directory).exists()
    return main, parsed, errors, notices


if __name__ == "__main__":
    block, parsed, errors, notices = run_data_block_example()
    print("Warning:", notices[0])
    print(type(block).__name__, block.data_name, type(block.data).__name__, len(block.data))
    print("Binary hex:", block.data.hex(), "Parsed:", parsed)
    print("Boundaries:", {name: type(value).__name__ if isinstance(value, CMADaaSError) else value
                          for name, value in errors.items()})
    print("All synthetic block contracts passed; no files written; temporary directory removed.")
