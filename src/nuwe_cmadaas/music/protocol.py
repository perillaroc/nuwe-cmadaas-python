"""Pure MUSIC URL and signature encoding helpers.

These helpers deliberately do not URL-escape values. Raw concatenation is a
compatibility requirement of the MUSIC protocol used by this package.
"""

from collections.abc import Mapping
from typing import Any


SENSITIVE_PARAMETER_NAMES = frozenset({"pwd", "password", "passwd"})


def encode_music_params(params: Mapping[str, Any]) -> str:
    """Encode parameters using MUSIC's original ``key=value`` text form."""
    for key in params:
        if str(key).lower() in SENSITIVE_PARAMETER_NAMES:
            raise ValueError(f"sensitive parameter is not allowed in MUSIC params: {key}")
    return "&".join(f"{key}={value}" for key, value in params.items())


def canonical_music_param_string(params: Mapping[str, Any]) -> str:
    """Return the sorted, unescaped canonical text used for signing."""
    return "&".join(f"{key}={params[key]}" for key in sorted(params, key=str))


def build_music_url(
    basic_url: str,
    *,
    method: str,
    user: str,
    interface_id: str,
    params: Mapping[str, Any],
    timestamp: str,
    nonce: str,
    sign: str,
) -> str:
    """Build the final MUSIC URL without applying generic URL encoding."""
    fixed = (
        f"method={method}&userId={user}&interfaceId={interface_id}"
        f"&language=Python&clientversion=V2.0.0"
    )
    parameter_text = encode_music_params(params)
    if parameter_text:
        fixed += "&" + parameter_text
    return f"{basic_url}{fixed}&timestamp={timestamp}&nonce={nonce}&sign={sign}"


def build_signature_params(
    params: Mapping[str, Any],
    *,
    service_node_id: str,
    method: str,
    user: str,
    interface_id: str,
    timestamp: str,
    nonce: str,
    password: str,
) -> dict[str, Any]:
    """Build the canonical signing mapping, including the private password."""
    result = dict(params)
    result.update({
        "serviceNodeId": service_node_id,
        "method": method,
        "userId": user,
        "interfaceId": interface_id,
        "language": "Python",
        "clientversion": "V2.0.0",
        "timestamp": timestamp,
        "nonce": nonce,
        "pwd": password,
    })
    return result


__all__ = [
    "build_music_url",
    "build_signature_params",
    "canonical_music_param_string",
    "encode_music_params",
]
