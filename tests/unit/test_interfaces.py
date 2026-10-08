import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import (
    InterfaceSpec,
    UnsupportedQueryError,
    resolve_interface,
)
from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.obs import download_obs_upper_air_file, retrieve_obs_upper_air
from tests.fixtures import (
    FakeCMADaaSClient,
    make_array2d_response,
    make_files_info_response,
    make_grid_array2d_response,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("family", "features", "interface_id", "return_type"),
    [
        (
            "model_grid_forecast",
            {"region", "time", "level", "valid_time", "number"},
            "getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember",
            "grid_array_2d",
        ),
        (
            "model_point",
            {"time", "level", "valid_time_range", "point"},
            "getNafpEleAtPointByTimeAndLevelAndValidtimeRange",
            "array_2d",
        ),
        (
            "model_file",
            {"element", "time", "level"},
            "getNafpFileByElementAndTimeAndLevel",
            "file_list",
        ),
        (
            "obs_station",
            {"region_region", "time_range"},
            "getSurfEleInRegionByTimeRange",
            "array_2d",
        ),
        (
            "obs_station",
            {"time", "station_range"},
            "getSurfEleByTimeAndStaIdRange",
            "array_2d",
        ),
        (
            "obs_grid",
            {"region", "time"},
            "getSurfEleGridInRectByTime",
            "grid_array_2d",
        ),
        (
            "obs_file",
            {"station", "time_range"},
            "getSurfFileByTimeRangeAndStaID",
            "file_list",
        ),
        (
            "obs_file_latest",
            set(),
            "getSurfLatestTime",
            "array_2d",
        ),
    ],
)
def test_registered_interface_spec_is_exact(family, features, interface_id, return_type):
    spec = resolve_interface(family, features)

    assert isinstance(spec, InterfaceSpec)
    assert spec.interface_id == interface_id
    assert spec.return_type == return_type
    assert spec.query_features == frozenset(features)


def test_unregistered_features_raise_without_creating_an_interface():
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface("model_grid_forecast", {"region", "number"})


def test_unregistered_model_grid_query_does_not_call_client():
    client = FakeCMADaaSClient(make_grid_array2d_response())
    region = {
        "type": "rect",
        "start_longitude": 110,
        "end_longitude": 111,
        "start_latitude": 30,
        "end_latitude": 31,
    }

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_model_grid(
            "SYNTHETIC_MODEL",
            parameter="TEM",
            region=region,
            number=1,
            client=client,
        )

    assert client.calls == []


def test_upper_air_query_uses_registered_interface():
    client = FakeCMADaaSClient(make_array2d_response())

    result = retrieve_obs_upper_air(
        data_code="UPAR_GLB_MUL_FTM",
        elements="Station_Id_d,TEM",
        time=pd.Timestamp("2026-01-02"),
        client=client,
    )

    assert isinstance(result, pd.DataFrame)
    assert client.calls[0][0] == "getUparEleByTime"


def test_upper_air_file_query_uses_registered_interface(tmp_path):
    client = FakeCMADaaSClient(make_files_info_response())

    download_obs_upper_air_file(
        "UPAR_GLB_MUL_FTM",
        time=pd.Timestamp("2026-01-02"),
        output_dir=tmp_path,
        client=client,
    )

    assert client.calls[0][0] == "getUparFileByTime"
