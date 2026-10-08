"""Surface-file routing and bounded-download regression checks."""

from pathlib import Path

import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface
from nuwe_cmadaas.obs import download_obs_file
from tests.fixtures import FakeCMADaaSClient, make_files_info_response
from tests.integration.obs.file.test_file import BoundedDownloadClient


pytestmark = pytest.mark.unit

BASE_TIME = (pd.Timestamp.now() - pd.Timedelta(days=2)).normalize()
TIME_RANGE = pd.Interval(BASE_TIME, BASE_TIME + pd.Timedelta(hours=1), closed="both")
RECT = {
    "type": "rect", "start_longitude": 115.7, "end_longitude": 117.4,
    "start_latitude": 41.6, "end_latitude": 39.4,
}
ADMIN = {"type": "region", "admin_codes": "110000"}
BASIN = {"type": "basin", "basin_codes": "CJLY"}


@pytest.mark.parametrize(
    ("station", "station_params"),
    [
        ("FAKE001", {"staIds": "FAKE001"}),
        (53592, {"staIds": 53592}),
        ([53592, "FAKE001"], {"staIds": "53592,FAKE001"}),
    ],
)
def test_supported_station_file_query_uses_catalog_interface(tmp_path, station, station_params):
    client = FakeCMADaaSClient(make_files_info_response())

    paths = download_obs_file(
        "SYNTHETIC_STATION", time=TIME_RANGE, station=station,
        count=2, output_dir=tmp_path, client=client,
    )

    assert paths == [Path(tmp_path, "synthetic.bin")]
    assert client.calls == [(
        "getSurfFileByTimeRangeAndStaID",
        {"dataCode": "SYNTHETIC_STATION", "timeRange": (
            f"[{BASE_TIME:%Y%m%d%H%M%S},{BASE_TIME + pd.Timedelta(hours=1):%Y%m%d%H%M%S}]"
        ),
         "limitCnt": 2, **station_params},
    )]


REMOVED_COMBINATIONS = [
    ((), {}),
    (("station",), {"station": "54511"}),
    (("station_range",), {"station": ("54511", "54512")}),
    (("station_level",), {"station_level": "011"}),
    (("station", "time"), {"station": "54511", "time": BASE_TIME}),
    (("station_range", "time"), {"station": ("54511", "54512"), "time": BASE_TIME}),
    (("station_range", "time_range"), {"station": ("54511", "54512"), "time": TIME_RANGE}),
    (("station_level", "time"), {"station_level": "011", "time": BASE_TIME}),
    (("station_level", "time_range"), {"station_level": "011", "time": TIME_RANGE}),
    (("region_rect",), {"region": RECT}),
    (("region_rect", "time"), {"region": RECT, "time": BASE_TIME}),
    (("region_rect", "time_range"), {"region": RECT, "time": TIME_RANGE}),
    (("region_region",), {"region": ADMIN}),
    (("region_region", "time"), {"region": ADMIN, "time": BASE_TIME}),
    (("region_region", "time_range"), {"region": ADMIN, "time": TIME_RANGE}),
    (("region_basin",), {"region": BASIN}),
    (("region_basin", "time"), {"region": BASIN, "time": BASE_TIME}),
    (("region_basin", "time_range"), {"region": BASIN, "time": TIME_RANGE}),
    (("region_rect", "station", "time"), {"region": RECT, "station": "54511", "time": BASE_TIME}),
    (("region_rect", "station", "time_range"), {"region": RECT, "station": "54511", "time": TIME_RANGE}),
    (("region_region", "station", "time"), {"region": ADMIN, "station": "54511", "time": BASE_TIME}),
    (("region_region", "station", "time_range"), {"region": ADMIN, "station": "54511", "time": TIME_RANGE}),
    (("region_basin", "station", "time"), {"region": BASIN, "station": "54511", "time": BASE_TIME}),
    (("region_basin", "station", "time_range"), {"region": BASIN, "station": "54511", "time": TIME_RANGE}),
]


@pytest.mark.parametrize(("features", "kwargs"), REMOVED_COMBINATIONS)
def test_catalog_absent_file_combination_is_rejected_before_request(
    tmp_path, features, kwargs
):
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface("obs_file", features)
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        download_obs_file(
            "SYNTHETIC_STATION", output_dir=tmp_path, client=client, **kwargs
        )

    assert client.calls == []


def test_download_obs_file_latest_time_does_not_delete_missing_optional_keys(tmp_path):
    client = FakeCMADaaSClient(make_files_info_response())

    download_obs_file(
        "SYNTHETIC_STATION", time=pd.Timedelta(hours=6),
        output_dir=tmp_path, client=client,
    )

    assert client.calls == [(
        "getSurfLatestTime",
        {"dataCode": "SYNTHETIC_STATION", "latestTime": "6"},
    )]


@pytest.mark.parametrize("count", [0, -1, 1.5, True])
def test_download_obs_file_rejects_invalid_count_without_request(tmp_path, count):
    client = FakeCMADaaSClient(make_files_info_response())

    with pytest.raises((TypeError, ValueError), match="count"):
        download_obs_file(
            "SYNTHETIC_STATION", time=BASE_TIME, count=count,
            output_dir=tmp_path, client=client,
        )

    assert client.calls == []


class RecordingFileClient:
    def __init__(self, listing):
        self.listing = listing
        self.calls = []

    def callAPI_to_fileList(self, interface_id, params):
        self.calls.append("list")
        return self.listing

    def callAPI_to_downFile(self, interface_id, params, file_dir):
        self.calls.append("download")
        return self.listing


@pytest.mark.parametrize("size, expected_calls", [("11", ["list"]), ("4", ["list", "download"])])
def test_file_preflight_blocks_oversize_download(tmp_path, size, expected_calls):
    listing = make_files_info_response(file_infos=[{
        "file_name": "synthetic.bin", "file_url": "https://synthetic.invalid/data.bin",
        "size": size,
    }])
    underlying = RecordingFileClient(listing)
    client = BoundedDownloadClient(underlying, max_files=1, max_total_bytes=10)

    if size == "11":
        with pytest.raises(AssertionError, match="exceeds"):
            download_obs_file("SYNTHETIC_STATION", time=BASE_TIME, output_dir=tmp_path, client=client)
    else:
        assert download_obs_file(
            "SYNTHETIC_STATION", time=BASE_TIME, output_dir=tmp_path, client=client
        ) == [Path(tmp_path, "synthetic.bin")]

    assert underlying.calls == expected_calls
