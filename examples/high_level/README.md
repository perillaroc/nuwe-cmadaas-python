# High-level examples

Run from the repository root after installing the main project (Python 3.11+):

```bash
uv run python -m examples.high_level.station
uv run python -m examples.high_level.grid
uv run python -m examples.high_level.upper_air
```

`station.py` uses synthetic protobuf responses and a real MUSIC client with
`SyntheticTransport`. It demonstrates a time query, a single station, a station
list with a time interval, a rectangle, and a latest-time table. It prints
tables, dtypes and attrs, converts numeric strings explicitly, and checks
expected values and rejection of latest-time filters before any request.

`grid.py` uses the same transport boundary for a 2 × 3 full field and a 2 × 2
rectangle. It prints coordinates, floating-point values, names, units and
request metadata, then checks both DataArrays and rejection of unsupported
time and region selectors before any request.

`upper_air.py` demonstrates conventional observations with pressure, height
and vertical selectors, GPS station/time-range requests, lightning events,
aircraft height ranges, and latest-time tables. It checks each branch's fields,
string values and attrs separately, including GPS `dataCode` differences and
rejection of invalid selectors before any request. Synthetic success does not
resolve the recorded GPS/lightning permissions or aircraft missing-data cases.

No credentials or external connections are needed. Unknown synthetic requests
fail immediately. The values, dates and station IDs are fictional, and the
responses do not demonstrate real service permissions or dataset capabilities.

The executable guides import `make_station_client()`, `make_grid_client()`
or `make_upper_air_client()`
and `check_results()` from their respective modules. Keep public calls in the
script and guide consistent when changing the tutorial. These repository examples and their
`examples/_support/` helpers are not included in the main package's wheel.
