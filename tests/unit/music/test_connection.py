import json

import pytest
import requests

from nuwe_cmadaas.music.connection import Connection
from nuwe_cmadaas.music.data import Array2D
from tests.fixtures import make_array2d_content


pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, content: bytes, status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}


class StreamingResponse:
    def __init__(self, chunks, status_code=200, headers=None, error=None):
        self.chunks = chunks
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/octet-stream"}
        self.error = error
        self.closed = False

    @property
    def content(self):
        raise AssertionError("streaming response content must not be read")

    def iter_content(self, chunk_size):
        for chunk in self.chunks:
            if isinstance(chunk, BaseException):
                raise chunk
            yield chunk

    def close(self):
        self.closed = True


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
    assert calls == [
        (
            "https://synthetic.invalid/file.bin",
            {"timeout": (1, 2), "stream": True},
        )
    ]


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


def test_download_file_creates_parent_directory(monkeypatch, tmp_path):
    connection = Connection(connect_timeout=1, read_timeout=2)
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(b"synthetic file content"),
    )

    result = connection.download_file(
        "https://synthetic.invalid/file.bin",
        tmp_path / "missing" / "synthetic.bin",
    )

    assert result == (0, None)
    assert (tmp_path / "missing" / "synthetic.bin").read_bytes() == b"synthetic file content"


def test_connection_accepts_injected_transport_and_retries_gateway_status():
    class Transport:
        def __init__(self):
            self.calls = []
            self.responses = [
                StreamingResponse([], status_code=503),
                FakeResponse(b"synthetic response"),
            ]

        def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return self.responses.pop(0)

    transport = Transport()
    sleeps = []
    connection = Connection(
        connect_timeout=1,
        read_timeout=2,
        transport=transport,
        max_retries=1,
        retry_backoff=0.5,
        sleep=sleeps.append,
    )

    result = connection.make_request(
        "https://synthetic.invalid/api",
        success_handler=lambda content: ("success", content),
        failure_handler=lambda content, **kwargs: ("failure", content),
        exception_handler=lambda error: ("exception", error),
    )

    assert result == ("success", b"synthetic response")
    assert len(transport.calls) == 2
    assert sleeps == [0.5]
    assert connection.last_retries == 1


def test_connection_does_not_retry_non_idempotent_request():
    class Transport:
        def __init__(self):
            self.calls = 0

        def get(self, url, **kwargs):
            self.calls += 1
            return FakeResponse(b"temporary service failure", status_code=503)

    transport = Transport()
    connection = Connection(1, 2, transport=transport, max_retries=2)
    response_data = Array2D()

    result = connection.make_request(
        "https://synthetic.invalid/api",
        success_handler=lambda content: content,
        failure_handler=Connection.generate_pack_failure_handler(response_data),
        exception_handler=Connection.generate_exception_handler(response_data),
        idempotent=False,
    )

    assert result is response_data
    assert transport.calls == 1
    assert response_data.request.error_code == Connection.httpError


def test_connection_classifies_non_2xx_text_without_exposing_body():
    connection = Connection(
        connect_timeout=1,
        read_timeout=2,
        transport=lambda: None,
        max_retries=0,
    )

    class Transport:
        def get(self, url, **kwargs):
            return FakeResponse(
                b"<html>synthetic secret response</html>", status_code=500
            )

    connection.transport = Transport()
    response_data = Array2D()
    result = connection.make_request(
        "https://synthetic.invalid/api",
        success_handler=lambda content: content,
        failure_handler=Connection.generate_pack_failure_handler(response_data),
        exception_handler=Connection.generate_exception_handler(response_data),
    )

    assert result is response_data
    assert response_data.request.error_code == Connection.httpError
    assert response_data.request.error_message == "HTTP 500 response"


def test_download_is_streamed_atomically_and_cleans_partial_file(tmp_path):
    destination = tmp_path / "synthetic.bin"
    destination.write_bytes(b"old content")
    response = StreamingResponse(
        [b"new ", requests.Timeout("synthetic read timeout")],
    )

    class Transport:
        def get(self, url, **kwargs):
            return response

    connection = Connection(
        connect_timeout=1,
        read_timeout=2,
        transport=Transport(),
        max_retries=0,
    )
    result = connection.download_file("https://synthetic.invalid/file", destination)

    assert result == (Connection.otherError, "request error")
    assert destination.read_bytes() == b"old content"
    assert list(tmp_path.glob("*.part")) == []
    assert response.closed


def test_download_retries_read_timeout_without_waiting_in_test(tmp_path):
    destination = tmp_path / "synthetic.bin"
    responses = [
        StreamingResponse([requests.Timeout("synthetic read timeout")]),
        StreamingResponse([b"complete content"], headers={"Content-Length": "16"}),
    ]
    calls = []

    class Transport:
        def get(self, url, **kwargs):
            calls.append(kwargs)
            return responses.pop(0)

    sleeps = []
    connection = Connection(
        connect_timeout=1,
        read_timeout=2,
        transport=Transport(),
        max_retries=1,
        retry_backoff=0.25,
        sleep=sleeps.append,
    )

    assert connection.download_file("https://synthetic.invalid/file", destination) == (0, None)
    assert destination.read_bytes() == b"complete content"
    assert calls == [
        {"timeout": (1, 2), "stream": True},
        {"timeout": (1, 2), "stream": True},
    ]
    assert sleeps == [0.25]


def test_download_can_protect_existing_target(tmp_path):
    destination = tmp_path / "synthetic.bin"
    destination.write_bytes(b"old content")
    connection = Connection(1, 2, transport=object(), max_retries=0)

    assert connection.download_file("https://synthetic.invalid/file", destination, overwrite=False) == (
        Connection.downloadError,
        "target file already exists",
    )
    assert destination.read_bytes() == b"old content"
