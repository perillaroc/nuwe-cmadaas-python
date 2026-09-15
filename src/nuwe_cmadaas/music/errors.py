"""Structured errors for the strict high-level CMADaaS API."""

from collections.abc import Mapping
from typing import Any
import warnings


_SECRET_NAMES = frozenset({"password", "passwd", "pwd", "sign", "token", "authorization"})


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: "<redacted>" if str(key).lower() in _SECRET_NAMES else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(_redact(item) for item in value)
    return value


class CMADaaSError(Exception):
    """Base class for errors raised by strict CMADaaS operations."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        server_message: str | None = None,
        interface_id: str | None = None,
        params: Mapping[str, Any] | None = None,
        request_id: str | None = None,
        retries: int = 0,
        cause: BaseException | None = None,
    ):
        self.error_code = error_code
        self.server_message = server_message
        self.interface_id = interface_id
        self.params = _redact(params) if params is not None else None
        self.request_id = request_id
        self.retries = retries
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        details = []
        if self.error_code is not None:
            details.append(f"code={self.error_code}")
        if self.interface_id is not None:
            details.append(f"interface={self.interface_id}")
        if self.server_message:
            details.append(f"message={self.server_message}")
        suffix = f" ({', '.join(details)})" if details else ""
        return f"{self.args[0]}{suffix}"


class CMADaaSConfigurationError(CMADaaSError):
    """Raised for invalid or incomplete client configuration."""


class CMADaaSQueryError(CMADaaSError):
    """Raised for an invalid high-level query."""


class CMADaaSTransportError(CMADaaSError):
    """Raised when a request cannot be sent or completed."""


class CMADaaSAuthenticationError(CMADaaSError):
    """Raised when CMADaaS rejects client authentication."""


class CMADaaSRequestError(CMADaaSError):
    """Raised for a non-zero MUSIC business or request error code."""


class CMADaaSDecodeError(CMADaaSError):
    """Raised when a response cannot be decoded as the expected payload."""


class CMADaaSDownloadError(CMADaaSError):
    """Raised when a file download fails."""


def error_from_request(
    request,
    *,
    interface_id: str | None = None,
    params: Mapping[str, Any] | None = None,
    cause: BaseException | None = None,
) -> CMADaaSError:
    """Create a typed exception from MUSIC ``RequestInfo`` metadata."""
    code = request.error_code
    error_type = CMADaaSRequestError
    if code == -1004:
        error_type = CMADaaSAuthenticationError
    elif code == -10001:
        error_type = CMADaaSTransportError
    return error_type(
        "CMADaaS request failed",
        error_code=code,
        server_message=request.error_message,
        interface_id=interface_id,
        params=params,
        cause=cause,
    )


def handle_response_error(
    response,
    *,
    interface_id: str,
    params: Mapping[str, Any] | None = None,
    strict: bool = False,
):
    """Raise a typed error or preserve the legacy ``MusicError`` result."""
    if response.ok:
        return None
    if strict:
        response.raise_for_error(interface_id=interface_id, params=params)
    warnings.warn(
        "Returning MusicError is retained for compatibility; use strict=True "
        "to receive a structured CMADaaS exception.",
        DeprecationWarning,
        stacklevel=3,
    )
    from .data import MusicError

    return MusicError(
        code=response.request.error_code,
        message=response.request.error_message,
    )


__all__ = [
    "CMADaaSError",
    "CMADaaSConfigurationError",
    "CMADaaSQueryError",
    "CMADaaSTransportError",
    "CMADaaSAuthenticationError",
    "CMADaaSRequestError",
    "CMADaaSDecodeError",
    "CMADaaSDownloadError",
    "error_from_request",
    "handle_response_error",
]
