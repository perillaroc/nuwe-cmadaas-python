"""Synthetic test data and test doubles for offline tests."""

from .clients import FakeCMADaaSClient
from .protobuf import (
    make_array2d_content,
    make_array2d_response,
    make_grid_array2d_content,
    make_grid_array2d_response,
    make_request_info,
)

__all__ = [
    "FakeCMADaaSClient",
    "make_array2d_content",
    "make_array2d_response",
    "make_grid_array2d_content",
    "make_grid_array2d_response",
    "make_request_info",
]
