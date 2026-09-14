# Offline test fixtures

All default data in this directory is manually designed synthetic data. It is
not recorded, copied, cropped, or transformed from a CMADaaS response.

- Station identifiers use the deliberately fictional `FAKE001` and `FAKE002`.
- Times, coordinates, values, and protobuf metadata are deterministic.
- Protobuf responses are generated in memory by `protobuf.py`; no binary
  response files or user configuration are needed.
- `FakeCMADaaSClient` records interface IDs and parameters and never opens a
  network connection.

Tests that need a real CMADaaS service must be marked `integration` and must
provide credentials outside the repository.
