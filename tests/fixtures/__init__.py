"""Synthetic test data and test doubles for offline tests."""

from .clients import FakeCMADaaSClient
from .protobuf import (
    make_array2d_content,
    make_array2d_response,
    make_grid_array2d_content,
    make_grid_array2d_response,
    make_grid_scalar2d_content,
    make_grid_scalar2d_response,
    make_grid_vector2d_content,
    make_grid_vector2d_response,
    make_files_info_content,
    make_files_info_response,
    make_data_block_content,
    make_data_block_response,
    make_request_info,
)

__all__ = [
    "FakeCMADaaSClient",
    "make_array2d_content",
    "make_array2d_response",
    "make_grid_array2d_content",
    "make_grid_array2d_response",
    "make_grid_scalar2d_content",
    "make_grid_scalar2d_response",
    "make_grid_vector2d_content",
    "make_grid_vector2d_response",
    "make_files_info_content",
    "make_files_info_response",
    "make_data_block_content",
    "make_data_block_response",
    "make_request_info",
]
