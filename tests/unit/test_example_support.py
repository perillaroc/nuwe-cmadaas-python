"""Exercise the documentation helpers through public library calls."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from examples._support import (
    FakeClient,
    SyntheticTransport,
    make_array2d_content,
    make_array2d_response,
    make_data_block_content,
    make_file_bytes,
    make_files_info_content,
    make_grid_array2d_content,
    make_grid_array2d_response,
    make_grid_scalar2d_content,
    make_grid_vector2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.music import CMADaaSClient
from nuwe_cmadaas.obs import download_obs_file, retrieve_obs_grid, retrieve_obs_station


pytestmark = pytest.mark.unit
TIME = pd.Timestamp("2026-01-02 00:00:00")
DATA_CODE = "SYNTHETIC_STATION"
FILE_URL = "https://synthetic.invalid/data.bin"


def test_fake_client_runs_public_high_level_conversions_and_rejects_unknown():
    client = FakeClient()
    station_params = {
        "dataCode": DATA_CODE,
        "elements": "Station_Id_C,Lat,Lon,TEM",
        "orderby": "Station_ID_d:asc",
        "times": "20260102000000",
    }
    grid_params = {
        "dataCode": "SYNTHETIC_GRID",
        "fcstEle": "synthetic_temperature",
        "time": "20260102000000",
    }
    client.register(
        "callAPI_to_array2D", "getSurfEleByTime", station_params,
        make_array2d_response(),
    )
    client.register(
        "callAPI_to_gridArray2D", "getSurfEleGridByTime", grid_params,
        make_grid_array2d_response(),
    )

    table = retrieve_obs_station(
        DATA_CODE, elements=station_params["elements"], time=TIME, client=client
    )
    field = retrieve_obs_grid(
        "SYNTHETIC_GRID", parameter="synthetic_temperature", time=TIME,
        client=client,
    )

    assert table.to_dict("records")[0]["Station_Id_C"] == "FAKE001"
    assert table["TEM"].tolist() == ["280.0", "281.5"]
    assert field.shape == (2, 3)
    assert field.name == "synthetic_temperature"
    assert client.calls == [
        ("callAPI_to_array2D", "getSurfEleByTime", station_params),
        ("callAPI_to_gridArray2D", "getSurfEleGridByTime", grid_params),
    ]
    with pytest.raises(AssertionError, match="unexpected fake client request"):
        retrieve_obs_station(
            DATA_CODE, elements=station_params["elements"],
            time=TIME + pd.Timedelta(hours=1), client=client,
        )


def test_transport_runs_real_client_decoders_for_table_and_three_grids():
    params = {"dataCode": "SYNTHETIC"}
    transport = SyntheticTransport()
    cases = (
        ("callAPI_to_array2D", "table", make_array2d_content()),
        ("callAPI_to_gridArray2D", "array-grid", make_grid_array2d_content()),
        ("callAPI_to_gridScalar2D", "scalar-grid", make_grid_scalar2d_content()),
        ("callAPI_to_gridVector2D", "vector-grid", make_grid_vector2d_content()),
        ("callAPI_to_dataBlock", "block", make_data_block_content()),
    )
    for method, interface_id, content in cases:
        transport.register_api(method, interface_id, params, content)
    client = make_synthetic_music_client(transport)

    table = client.callAPI_to_array2D("table", params).to_pandas()
    array_grid = client.callAPI_to_gridArray2D("array-grid", params).to_xarray()
    scalar_grid = client.callAPI_to_gridScalar2D("scalar-grid", params).to_xarray()
    vector_grid = client.callAPI_to_gridVector2D("vector-grid", params).to_xarray()
    with pytest.warns(UserWarning, match="no verified live-service interface"):
        block = client.callAPI_to_dataBlock("block", params)

    assert table.iloc[0]["Station_Id_C"] == "FAKE001"
    np.testing.assert_array_equal(array_grid, scalar_grid)
    assert array_grid.shape == scalar_grid.shape == (2, 3)
    assert set(vector_grid.data_vars) == {"synthetic_u_wind", "synthetic_v_wind"}
    assert block.data == b"synthetic payload"
    assert len(transport.calls) == len(cases)
    assert all(response.closed for response in transport.responses)


def test_transport_runs_real_client_file_list_download_save_and_text(tmp_path):
    params = {"dataCode": "SYNTHETIC"}
    transport = SyntheticTransport()
    transport.register_api(
        "callAPI_to_fileList", "files", params, make_files_info_content()
    )
    target = tmp_path / "saved.bin"
    transport.register_api(
        "callAPI_to_saveAsFile", "save", {
            **params, "dataFormat": "text", "savepath": str(target),
        }, make_files_info_content(),
    )
    transport.register_api(
        "callAPI_to_serializedStr", "text", {
            **params, "dataFormat": "text",
        }, b"synthetic text",
    )
    transport.register_download(FILE_URL, make_file_bytes())
    client = make_synthetic_music_client(transport)

    listing = client.callAPI_to_fileList("files", params)
    assert listing.ok
    assert listing.files_info[0].size == str(len(make_file_bytes()))
    assert list(tmp_path.iterdir()) == []

    downloaded = client.callAPI_to_downFile("files", params, tmp_path)
    assert downloaded.ok
    assert (tmp_path / "synthetic.bin").read_bytes() == make_file_bytes()

    saved = client.callAPI_to_saveAsFile("save", params.copy(), "text", str(target))
    assert saved.ok
    assert target.read_bytes() == make_file_bytes()

    text_params = params.copy()
    assert client.callAPI_to_serializedStr("text", text_params, "text") == "synthetic text"
    assert text_params["dataFormat"] == "text"
    assert len([response for response in transport.responses if response.streamed]) == 2
    assert all(response.closed for response in transport.responses)


def test_real_client_transport_supports_public_file_download(tmp_path):
    params = {"dataCode": DATA_CODE, "times": "20260102000000"}
    transport = SyntheticTransport()
    transport.register_api(
        "callAPI_to_fileList", "getSurfFileByTime", params,
        make_files_info_content(),
    )
    transport.register_download(FILE_URL, make_file_bytes())
    client = make_synthetic_music_client(transport)

    paths = download_obs_file(
        DATA_CODE, time=TIME, output_dir=tmp_path, client=client, strict=True
    )

    assert paths == [Path(tmp_path / "synthetic.bin")]
    assert paths[0].read_bytes() == make_file_bytes()
    assert len(transport.calls) == 2


def test_transport_and_session_reject_unknown_requests_without_network():
    transport = SyntheticTransport()
    client = make_synthetic_music_client(transport)

    with pytest.raises(AssertionError, match="unexpected synthetic MUSIC request"):
        client.callAPI_to_array2D("unknown", {"dataCode": "SYNTHETIC"})
    with pytest.raises(AssertionError, match="unexpected synthetic transport URL"):
        transport.get("https://synthetic.invalid/missing.bin", stream=True)

    transport.register_api(
        "callAPI_to_array2D", "known", {"dataCode": "SYNTHETIC"},
        make_array2d_content(),
    )
    session_client = CMADaaSClient(
        server_ip="synthetic.invalid", server_port=80,
        server_id="synthetic-service", connection_timeout=1, read_timeout=1,
        user="synthetic-user", password="synthetic-password",
        session=transport, max_retries=0,
    )
    assert session_client.callAPI_to_array2D(
        "known", {"dataCode": "SYNTHETIC"}
    ).to_pandas().shape == (2, 4)
