"""Strict response client for high-level documentation examples."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from nuwe_cmadaas.music.data import Array2D, FilesInfo, GridArray2D


_RESPONSE_TYPES = {
    "callAPI_to_array2D": Array2D,
    "callAPI_to_gridArray2D": GridArray2D,
    "callAPI_to_fileList": FilesInfo,
    "callAPI_to_downFile": FilesInfo,
}


def _parameter_key(params: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """Match the text values that the MUSIC client sends on the wire."""

    return tuple(sorted((str(name), str(value)) for name, value in params.items()))


class FakeClient:
    """Return registered response objects to public high-level functions.

    Register the exact method, interface ID and MUSIC parameters expected from
    a tutorial call. Unknown requests raise immediately; no network fallback
    or high-level function mocking is involved.
    """

    def __init__(self) -> None:
        self._responses: dict[tuple[str, str, tuple[tuple[str, str], ...]], Any] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def register(
        self,
        method: str,
        interface_id: str,
        params: Mapping[str, Any],
        response: Array2D | GridArray2D | FilesInfo,
    ) -> None:
        expected_type = _RESPONSE_TYPES.get(method)
        if expected_type is None:
            raise ValueError(f"unsupported fake client method: {method}")
        if not isinstance(response, expected_type):
            raise TypeError(f"{method} requires {expected_type.__name__}")
        key = (method, interface_id, _parameter_key(params))
        if key in self._responses:
            raise ValueError(f"duplicate fake client route: {method}/{interface_id}")
        self._responses[key] = response

    def _dispatch(self, method: str, interface_id: str, params: Mapping[str, Any]):
        self.calls.append((method, interface_id, dict(params)))
        key = (method, interface_id, _parameter_key(params))
        try:
            return self._responses[key]
        except KeyError:
            raise AssertionError(
                f"unexpected fake client request: {method}/{interface_id} "
                f"with params {dict(params)!r}"
            ) from None

    def callAPI_to_array2D(self, interface_id, params, server_id=None):
        return self._dispatch("callAPI_to_array2D", interface_id, params)

    def callAPI_to_gridArray2D(self, interface_id, params, server_id=None):
        return self._dispatch("callAPI_to_gridArray2D", interface_id, params)

    def callAPI_to_fileList(self, interface_id, params, server_id=None):
        return self._dispatch("callAPI_to_fileList", interface_id, params)

    def callAPI_to_downFile(
        self, interface_id, params, file_dir: str | Path, server_id=None
    ):
        return self._dispatch("callAPI_to_downFile", interface_id, params)
