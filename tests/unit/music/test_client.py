import pytest
import requests

from nuwe_cmadaas.music.client import CMADaaSClient
from nuwe_cmadaas.music.connection import Connection
from nuwe_cmadaas.music.protocol import encode_music_params
from tests.fixtures import (
    make_array2d_content,
    make_files_info_content,
    make_grid_array2d_content,
)


pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content


def make_client():
    return CMADaaSClient(
        server_ip="synthetic.example",
        server_port=8080,
        server_id="synthetic-service",
        connection_timeout=1.25,
        read_timeout=4.5,
        user="synthetic-user",
        password="synthetic-password",
    )


def test_call_api_to_array2d_decodes_synthetic_response(monkeypatch):
    client = make_client()
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(make_array2d_content())

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)

    result = client.callAPI_to_array2D(
        "syntheticInterface",
        {"dataCode": "SYNTHETIC"},
    )

    assert result.data.shape == (2, 4)
    assert result.request.error_code == 0
    assert len(calls) == 1
    assert calls[0][1] == {"timeout": (1.25, 4.5), "stream": True}


def test_call_api_to_array2d_preserves_gateway_business_error(monkeypatch):
    client = make_client()
    gateway_error = (
        b'{"returnCode":-1004,"flag":"slb",'
        b'"returnMessage":"Synthetic authentication failure"}'
    )
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(gateway_error),
    )

    result = client.callAPI_to_array2D(
        "syntheticInterface",
        {"dataCode": "SYNTHETIC"},
    )

    assert result.request.error_code == -1004
    assert result.request.error_message == "Synthetic authentication failure"


def test_call_api_to_serialized_str_returns_success_content(monkeypatch):
    client = make_client()
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResponse(b"synthetic serialized response")

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)
    params = {"dataCode": "SYNTHETIC"}

    result = client.callAPI_to_serializedStr(
        "syntheticInterface",
        params,
        "json",
    )

    assert result == "synthetic serialized response"
    assert params["dataFormat"] == "json"
    assert "dataFormat=json" in calls[0]


def test_call_api_to_serialized_str_returns_gateway_error(monkeypatch):
    client = make_client()
    gateway_error = (
        b'{"returnCode":-1004,"flag":"slb",'
        b'"returnMessage":"Synthetic authentication failure"}'
    )
    monkeypatch.setattr(
        "nuwe_cmadaas.music.connection.requests.get",
        lambda *args, **kwargs: FakeResponse(gateway_error),
    )

    result = client.callAPI_to_serializedStr(
        "syntheticInterface",
        {},
        "json",
    )

    assert "returnCode=-1004" in result
    assert "Synthetic authentication failure" in result


def test_call_api_to_serialized_str_handles_timeout(monkeypatch):
    client = make_client()

    def fake_get(*args, **kwargs):
        raise requests.Timeout("synthetic timeout")

    monkeypatch.setattr("nuwe_cmadaas.music.connection.requests.get", fake_get)

    result = client.callAPI_to_serializedStr(
        "syntheticInterface",
        {},
        "json",
    )

    assert result == "Error retrieving data"


def test_fetch_url_has_reproducible_signature_and_no_plain_password(monkeypatch):
    client = make_client()
    monkeypatch.setattr(
        "nuwe_cmadaas.music.client.time.time",
        lambda: 1700000000.123,
    )
    monkeypatch.setattr(
        "nuwe_cmadaas.music.client.uuid.uuid1",
        lambda: "synthetic-nonce",
    )

    url = client._get_fetch_url(
        "syntheticInterface",
        "callAPI_to_serializedStr",
        {"dataCode": "SYNTHETIC"},
    )

    assert url == (
        "http://synthetic.example:8080/music-ws/api?"
        "serviceNodeId=synthetic-service&method=callAPI_to_serializedStr&"
        "userId=synthetic-user&interfaceId=syntheticInterface&language=Python&"
        "clientversion=V2.0.0&dataCode=SYNTHETIC&timestamp=1700000000123&"
        "nonce=synthetic-nonce&sign=353B9D4703150D3384281D3B63E8D1E3"
    )
    assert "synthetic-password" not in url


def test_music_parameter_encoding_preserves_raw_compatibility_text():
    params = {"text": 'a b&中文+"[]'}

    assert encode_music_params(params) == 'text=a b&中文+"[]'


@pytest.mark.parametrize("policy", ["full", "redacted", "summary"])
def test_log_policies_never_log_password(monkeypatch, policy):
    messages = []
    monkeypatch.setattr(
        "nuwe_cmadaas.music.client.logger.info",
        lambda message: messages.append(message),
    )

    class Transport:
        def get(self, url, **kwargs):
            return FakeResponse(make_array2d_content())

    client = CMADaaSClient(
        server_ip="synthetic.example",
        server_port=8080,
        server_id="synthetic-service",
        connection_timeout=1,
        read_timeout=2,
        user="synthetic-user",
        password="synthetic-password",
        transport=Transport(),
        log_policy=policy,
        max_retries=0,
    )

    client.callAPI_to_array2D("syntheticInterface", {"dataCode": "SYNTHETIC"})

    assert messages
    assert all("synthetic-password" not in message for message in messages)
    if policy == "full":
        assert "userId=synthetic-user" in messages[0]
    elif policy == "redacted":
        assert "synthetic-user" not in messages[0]
        assert "sign=<redacted>" in messages[0]
    else:
        assert "request summary" in messages[0]
        assert "interface=syntheticInterface" in messages[0]
        assert "service_node=synthetic-service" in messages[0]
        assert "result_code=0" in messages[0]
        assert "retries=0" in messages[0]


def test_full_log_url_is_the_url_sent_to_transport(monkeypatch):
    messages = []
    calls = []
    monkeypatch.setattr(
        "nuwe_cmadaas.music.client.logger.info",
        lambda message: messages.append(message),
    )

    class Transport:
        def get(self, url, **kwargs):
            calls.append(url)
            return FakeResponse(make_array2d_content())

    client = CMADaaSClient(
        server_ip="synthetic.example",
        server_port=8080,
        server_id="synthetic-service",
        connection_timeout=1,
        read_timeout=2,
        user="synthetic-user",
        password="synthetic-password",
        transport=Transport(),
        log_policy="full",
        max_retries=0,
    )
    client.callAPI_to_array2D("syntheticInterface", {"dataCode": "SYNTHETIC"})

    assert messages == [f"fetch url: {calls[0]}"]


def test_download_rejects_server_path_traversal_before_file_request(tmp_path):
    calls = []

    class Transport:
        def get(self, url, **kwargs):
            calls.append(url)
            return FakeResponse(
                make_files_info_content(
                    file_infos=[
                        {
                            "file_name": "../outside.bin",
                            "file_url": "https://synthetic.invalid/file",
                        }
                    ]
                )
            )

    client = CMADaaSClient(
        server_ip="synthetic.example",
        server_port=8080,
        server_id="synthetic-service",
        connection_timeout=1,
        read_timeout=2,
        user="synthetic-user",
        password="synthetic-password",
        transport=Transport(),
        max_retries=0,
    )

    result = client.callAPI_to_downFile("syntheticInterface", {}, tmp_path)

    assert result.request.error_code == Connection.downloadError
    assert result.request.error_message == "unsafe server file name"
    assert len(calls) == 1
    assert not (tmp_path.parent / "outside.bin").exists()


def test_grid_output_carries_query_metadata_without_changing_values():
    class Transport:
        def get(self, url, **kwargs):
            return FakeResponse(make_grid_array2d_content())

    client = CMADaaSClient(
        server_ip="synthetic.example",
        server_port=8080,
        server_id="synthetic-service",
        connection_timeout=1,
        read_timeout=2,
        user="synthetic-user",
        password="synthetic-password",
        transport=Transport(),
        max_retries=0,
    )
    result = client.callAPI_to_gridArray2D(
        "syntheticInterface",
        {
            "time": "20260102000000",
            "validTime": "24",
            "levelType": "100",
            "fcstLevel": "850",
            "fcstMember": 2,
        },
    )

    field = result.to_xarray()
    assert field.attrs["interface_id"] == "syntheticInterface"
    assert field.attrs["time"] == "20260102000000"
    assert field.attrs["valid_time"] == "24"
    assert field.attrs["level_type"] == "100"
    assert field.attrs["level"] == "850"
    assert field.attrs["member"] == 2
