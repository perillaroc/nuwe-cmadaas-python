import json

import pytest
import requests

from nuwe_cmadaas.music.connection import Connection
from nuwe_cmadaas.music.data import Array2D
from tests.fixtures import make_array2d_content


pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content


def gateway_error_content():
    return json.dumps(
        {
            "returnCode": -1004,
            "flag": "slb",
            "returnMessage": "Synthetic authentication failure",
        }
    ).encode()


def test_make_request_passes_url_timeout_and_stream(monkeypatch):
    connection = Connection(connect_timeout=1.25, read_timeout=4.5)
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(make_array2d_content())

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)

    result = connection.make_request(
        "http://synthetic.invalid/api",
        success_handler=lambda content: ("success", content),
        failure_handler=lambda content: ("failure", content),
        exception_handler=lambda error: ("exception", error),
    )

    assert result[0] == "success"
    assert result[1] == make_array2d_content()
    assert calls == [
        (
            "http://synthetic.invalid/api",
            {"timeout": (1.25, 4.5), "stream": True},
        )
    ]


def test_make_request_routes_gateway_json_to_failure_handler(monkeypatch):
    connection = Connection(connect_timeout=1, read_timeout=2)
    response_data = Array2D()
    success_called = False

    def success_handler(content):
        nonlocal success_called
        success_called = True
        return content

    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(gateway_error_content()),
    )

    result = connection.make_request(
        "http://synthetic.invalid/api",
        success_handler=success_handler,
        failure_handler=Connection.generate_pack_failure_handler(response_data),
        exception_handler=Connection.generate_exception_handler(response_data),
    )

    assert result is response_data
    assert not success_called
    assert response_data.request.error_code == -1004
    assert response_data.request.error_message == "Synthetic authentication failure"


@pytest.mark.parametrize("error", [requests.Timeout("synthetic timeout"), requests.ConnectionError("synthetic connection")])
def test_make_request_routes_network_errors_to_exception_handler(monkeypatch, error):
    connection = Connection(connect_timeout=1, read_timeout=2)
    response_data = Array2D()

    def fake_get(*args, **kwargs):
        raise error

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)

    result = connection.make_request(
        "http://synthetic.invalid/api",
        success_handler=lambda content: content,
        failure_handler=lambda content: content,
        exception_handler=Connection.generate_exception_handler(response_data),
    )

    assert result is response_data
    assert response_data.request.error_code == Connection.otherError
    assert response_data.request.error_message == "Error retrieving data"


def test_download_file_writes_synthetic_content(monkeypatch, tmp_path):
    connection = Connection(connect_timeout=1, read_timeout=2)
    destination = tmp_path / "synthetic.bin"
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(b"synthetic file content")

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)

    result = connection.download_file(
        "https://synthetic.invalid/file.bin",
        destination,
    )

    assert result == (0, None)
    assert destination.read_bytes() == b"synthetic file content"
    assert calls == [("https://synthetic.invalid/file.bin", {"stream": True})]


def test_download_file_returns_gateway_error_without_writing(monkeypatch, tmp_path):
    connection = Connection(connect_timeout=1, read_timeout=2)
    destination = tmp_path / "synthetic.bin"
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(gateway_error_content()),
    )

    result = connection.download_file("https://synthetic.invalid/file.bin", destination)

    assert result == (-1004, "Synthetic authentication failure")
    assert not destination.exists()


def test_download_file_returns_request_error(monkeypatch, tmp_path):
    connection = Connection(connect_timeout=1, read_timeout=2)
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            requests.ConnectionError("synthetic connection")
        ),
    )

    result = connection.download_file(
        "https://synthetic.invalid/file.bin",
        tmp_path / "synthetic.bin",
    )

    assert result == (Connection.otherError, "request error")


def test_download_file_returns_io_error(monkeypatch, tmp_path):
    connection = Connection(connect_timeout=1, read_timeout=2)
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(b"synthetic file content"),
    )

    result = connection.download_file(
        "https://synthetic.invalid/file.bin",
        tmp_path / "missing" / "synthetic.bin",
    )

    assert result == (Connection.otherError, "create file error")
