# High-level examples

Run from the repository root after installing the main project (Python 3.11+):

```bash
uv run python -m examples.high_level.station
```

`station.py` uses synthetic protobuf responses and a real MUSIC client with
`SyntheticTransport`. It demonstrates a time query, a single station, a station
list with a time interval, a rectangle, and a latest-time table. It prints
tables, dtypes and attrs, converts numeric strings explicitly, and checks
expected values and rejection of latest-time filters before any request.

No credentials or external connections are needed. Unknown synthetic requests
fail immediately. The values, dates and station IDs are fictional, and the
responses do not demonstrate real service permissions or dataset capabilities.

The executable surface-station guide imports `make_station_client()` and
`check_results()` from this module. Keep public calls in the script and guide
consistent when changing the tutorial. These repository examples and their
`examples/_support/` helpers are not included in the main package's wheel.
