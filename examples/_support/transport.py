"""In-memory MUSIC HTTP transport for executable offline examples."""

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from nuwe_cmadaas.music import CMADaaSClient

from .clients import _parameter_key


_FIXED_QUERY_KEYS = frozenset({
    "serviceNodeId", "method", "userId", "interfaceId", "language",
    "clientversion", "timestamp", "nonce", "sign",
})


class SyntheticResponse:
    """A minimal response that supports protobuf reads and streamed files."""

    def __init__(self, content: bytes, *, download: bool = False) -> None:
        self._content = content
        self._download = download
        self.status_code = 200
        self.headers = {
            "Content-Type": (
                "application/octet-stream" if download else "application/x-protobuf"
            ),
            "Content-Length": str(len(content)),
        }
        self.closed = False
        self.streamed = False

    @property
    def content(self) -> bytes:
        if self._download:
            raise AssertionError("synthetic download must use iter_content")
        return self._content

    def iter_content(self, chunk_size: int):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.streamed = True
        for index in range(0, len(self._content), chunk_size):
            yield self._content[index:index + chunk_size]

    def close(self) -> None:
        self.closed = True


class SyntheticTransport:
    """Serve only explicitly registered synthetic API and file URLs."""

    def __init__(self) -> None:
        self._api_responses: dict[
            tuple[str, str, tuple[tuple[str, str], ...]], bytes
        ] = {}
        self._downloads: dict[str, bytes] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses: list[SyntheticResponse] = []

    def register_api(
        self,
        method: str,
        interface_id: str,
        params: Mapping[str, Any],
        content: bytes,
    ) -> None:
        if not isinstance(content, bytes):
            raise TypeError("API content must be bytes")
        if _FIXED_QUERY_KEYS.intersection(params):
            raise ValueError("API params must not contain MUSIC envelope fields")
        key = (method, interface_id, _parameter_key(params))
        if key in self._api_responses:
            raise ValueError(f"duplicate synthetic API route: {method}/{interface_id}")
        self._api_responses[key] = content

    def register_download(self, url: str, content: bytes) -> None:
        if urlsplit(url).hostname != "synthetic.invalid":
            raise ValueError("synthetic download URL must use synthetic.invalid")
        if not isinstance(content, bytes):
            raise TypeError("download content must be bytes")
        if url in self._downloads:
            raise ValueError(f"duplicate synthetic download URL: {url}")
        self._downloads[url] = content

    @staticmethod
    def _parse_api_url(url: str) -> tuple[str, str, tuple[tuple[str, str], ...]]:
        parts = urlsplit(url)
        if parts.hostname != "synthetic.invalid" or parts.path != "/music-ws/api":
            raise AssertionError("unexpected synthetic transport URL")
        query: dict[str, str] = {}
        for field in parts.query.split("&"):
            if "=" not in field:
                raise AssertionError("malformed synthetic MUSIC query")
            name, value = field.split("=", 1)
            if name in query:
                raise AssertionError(f"duplicate synthetic MUSIC parameter: {name}")
            query[name] = value
        if query.get("userId") != "synthetic-user":
            raise AssertionError("unexpected synthetic MUSIC user")
        if query.get("serviceNodeId") != "synthetic-service":
            raise AssertionError("unexpected synthetic MUSIC service node")
        if not all(query.get(name) for name in ("method", "interfaceId", "timestamp", "nonce", "sign")):
            raise AssertionError("incomplete synthetic MUSIC request")
        params = {name: value for name, value in query.items() if name not in _FIXED_QUERY_KEYS}
        return query["method"], query["interfaceId"], _parameter_key(params)

    def get(self, url: str, **kwargs) -> SyntheticResponse:
        self.calls.append((url, dict(kwargs)))
        if kwargs.get("stream") is not True:
            raise AssertionError("synthetic requests must be streamed")
        if url in self._downloads:
            response = SyntheticResponse(self._downloads[url], download=True)
        else:
            key = self._parse_api_url(url)
            try:
                content = self._api_responses[key]
            except KeyError:
                raise AssertionError(
                    f"unexpected synthetic MUSIC request: {key[0]}/{key[1]} "
                    f"with params {dict(key[2])!r}"
                ) from None
            response = SyntheticResponse(content)
        self.responses.append(response)
        return response


def make_synthetic_music_client(transport: SyntheticTransport) -> CMADaaSClient:
    """Create a real MUSIC client wired only to the synthetic transport."""

    return CMADaaSClient(
        server_ip="synthetic.invalid",
        server_port=80,
        server_id="synthetic-service",
        connection_timeout=1,
        read_timeout=1,
        user="synthetic-user",
        password="synthetic-password",
        transport=transport,
        log_policy="summary",
        max_retries=0,
    )
