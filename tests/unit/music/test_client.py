import pytest
import requests

from nuwe_cmadaas.music.client import CMADaaSClient
from tests.fixtures import make_array2d_content


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
