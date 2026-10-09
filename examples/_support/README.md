# Synthetic response factories

`synthetic.py` builds small, deterministic MUSIC protobuf messages and decodes
them into the library's response classes. It uses fictional station IDs,
fixed request timestamps, a 2 × 3 grid, a four-byte file body, and a
`.invalid` file URL. No factory reads credentials, connects to CMADaaS, or
uses captured service output.

From the repository root, import factories such as
`examples._support.make_array2d_response` or
`examples._support.make_grid_vector2d_response`. The default
`make_files_info_response()` reports the size of `make_file_bytes()`; C04 will
use both when building the simulated download transport.

The `tests.fixtures.protobuf` module re-exports the same functions for old
offline tests. This helper package is outside `src/` and is not distributed
with `nuwe_cmadaas`.
