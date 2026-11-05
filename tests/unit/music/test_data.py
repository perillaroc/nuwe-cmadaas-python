import numpy as np
import pytest

from nuwe_cmadaas.music.data import (
    Array2D,
    DataBlock,
    FileInfo,
    FilesInfo,
    GridArray2D,
    GridScalar2D,
    GridVector2D,
)
from tests.fixtures import (
    make_array2d_content,
    make_data_block_content,
    make_files_info_content,
    make_grid_array2d_content,
    make_grid_scalar2d_content,
    make_grid_vector2d_content,
)
from nuwe_cmadaas.music.errors import CMADaaSError


pytestmark = pytest.mark.unit


def test_response_containers_have_stable_empty_defaults():
    assert Array2D().data.shape == (0, 0)
    assert Array2D().element_names == []
    assert DataBlock().data == b""
    assert FilesInfo().files_info == []
    assert FileInfo().attributes == []
    assert GridArray2D().data.shape == (0, 0)
    assert GridArray2D().lats == []
    assert GridArray2D().lons == []
    assert GridScalar2D().data.shape == (0, 0)
    assert GridVector2D().u_datas.shape == (0, 0)
    assert GridVector2D().v_datas.shape == (0, 0)


def test_empty_successful_grid_is_a_valid_empty_xarray():
    field = GridArray2D().to_xarray()

    assert field.shape == (0, 0)
    assert field.dims == ("latitude", "longitude")
    assert field.sizes == {"latitude": 0, "longitude": 0}


def test_error_response_cannot_be_converted_as_empty_data():
    response = GridArray2D.create_from_protobuf(
        make_grid_array2d_content(
            error_code=-1004,
            error_message="Synthetic authentication failure",
        )
    )

    assert response.data.shape == (0, 0)
    with pytest.raises(CMADaaSError):
        response.to_xarray()


def test_array2d_decodes_protobuf_and_converts_to_pandas():
    result = Array2D.create_from_protobuf(make_array2d_content())

    assert result.request.error_code == 0
    assert result.request.request_time == "20260102000000"
    assert result.row_count == 2
    assert result.col_count == 4
    assert result.data.shape == (2, 4)
    assert result.to_pandas().to_dict("records") == [
        {
            "Station_Id_C": "FAKE001",
            "Lat": "30.0",
            "Lon": "110.0",
            "TEM": "280.0",
        },
        {
            "Station_Id_C": "FAKE002",
            "Lat": "31.0",
            "Lon": "111.0",
            "TEM": "281.5",
        },
    ]


def test_grid_array2d_decodes_protobuf_and_converts_to_xarray():
    result = GridArray2D.create_from_protobuf(make_grid_array2d_content())
    field = result.to_xarray()

    assert result.request.row_count == 2
    assert result.request.col_count == 3
    assert result.data.shape == (2, 3)
    assert field.name == "synthetic_temperature"
    assert field.attrs["units"] == "K"
    assert field.attrs["request_time"] == "20260102000000"
    assert field.dims == ("latitude", "longitude")
    np.testing.assert_array_equal(field.latitude, [30.0, 31.0])
    np.testing.assert_array_equal(field.longitude, [110.0, 111.0, 112.0])
    np.testing.assert_allclose(
        field.values,
        [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]],
    )


def test_grid_scalar2d_decodes_datas_field():
    result = GridScalar2D.create_from_protobuf(
        make_grid_scalar2d_content(
            lats=[30.0, 31.0],
            lons=[110.0, 111.0, 112.0],
        )
    )

    assert result.request.error_code == 0
    assert result.user_element_name == "synthetic_temperature"
    assert result.units == "K"
    assert result.data.shape == (2, 3)
    np.testing.assert_allclose(
        result.data,
        [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]],
    )


def test_grid_scalar2d_converts_to_xarray_with_frozen_contract():
    field = GridScalar2D.create_from_protobuf(
        make_grid_scalar2d_content()
    ).to_xarray()

    assert field.name == "synthetic_temperature"
    assert field.dims == ("latitude", "longitude")
    assert field.shape == (2, 3)
    assert field.attrs["units"] == "K"
    np.testing.assert_array_equal(field.latitude, [30.0, 31.0])
    np.testing.assert_array_equal(field.longitude, [110.0, 111.0, 112.0])


def test_grid_vector2d_decodes_both_components():
    result = GridVector2D.create_from_protobuf(
        make_grid_vector2d_content(
            lats=[30.0, 31.0],
            lons=[110.0, 111.0, 112.0],
        )
    )

    assert result.request.error_code == 0
    assert result.u_element_name == "synthetic_u_wind"
    assert result.v_element_name == "synthetic_v_wind"
    np.testing.assert_allclose(
        result.u_datas,
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
    )
    np.testing.assert_allclose(
        result.v_datas,
        [[-1.0, -2.0, -3.0], [-4.0, -5.0, -6.0]],
    )


def test_grid_vector2d_converts_to_xarray_dataset():
    dataset = GridVector2D.create_from_protobuf(
        make_grid_vector2d_content()
    ).to_xarray()

    assert set(dataset.data_vars) == {"synthetic_u_wind", "synthetic_v_wind"}
    assert dataset["synthetic_u_wind"].dims == ("latitude", "longitude")
    assert dataset["synthetic_u_wind"].shape == (2, 3)
    np.testing.assert_array_equal(dataset.latitude, [30.0, 31.0])
    np.testing.assert_array_equal(dataset.longitude, [110.0, 111.0, 112.0])


def test_files_info_and_data_block_decode_protobuf():
    files = FilesInfo.create_from_protobuf(make_files_info_content())
    block = DataBlock.create_from_protobuf(make_data_block_content())

    assert files.request.error_code == 0
    assert len(files.files_info) == 1
    assert files.files_info[0].file_name == "synthetic.bin"
    assert files.files_info[0].file_url == "https://synthetic.invalid/data.bin"
    assert files.files_info[0].attributes == ["synthetic", "offline"]
    assert block.request.error_code == 0
    assert block.data_name == "synthetic_block"
    assert block.data == b"synthetic payload"


@pytest.mark.parametrize(
    ("response_type", "content_factory"),
    [
        (Array2D, make_array2d_content),
        (GridArray2D, make_grid_array2d_content),
        (GridScalar2D, make_grid_scalar2d_content),
        (GridVector2D, make_grid_vector2d_content),
        (FilesInfo, make_files_info_content),
        (DataBlock, make_data_block_content),
    ],
)
def test_nonzero_protobuf_error_is_preserved(response_type, content_factory):
    result = response_type.create_from_protobuf(
        content_factory(
            error_code=-1004,
            error_message="Synthetic authentication failure",
        )
    )

    assert result.request.error_code == -1004
    assert result.request.error_message == "Synthetic authentication failure"


def test_array2d_rejects_data_length_mismatch():
    with pytest.raises(ValueError, match="Array2D data length"):
        Array2D.create_from_protobuf(
            make_array2d_content(row_count=3, col_count=4)
        )


def test_grid_array2d_rejects_data_length_mismatch():
    with pytest.raises(ValueError, match="GridArray2D data length"):
        GridArray2D.create_from_protobuf(
            make_grid_array2d_content(
                lat_count=2, lon_count=4,
                lons=[110.0, 111.0, 112.0, 113.0],
            )
        )


def test_grid_array2d_rejects_coordinate_length_mismatch():
    with pytest.raises(ValueError, match="latitude coordinate length"):
        GridArray2D.create_from_protobuf(
            make_grid_array2d_content(lats=[30.0], lat_count=2)
        )


def test_float32_header_step_drift_uses_declared_endpoints():
    response = GridArray2D(
        data=np.arange(201 * 201, dtype=float).reshape(201, 201),
        start_lat=41.0, end_lat=39.0, lat_step=-0.009998321533203125,
        start_lon=115.0, end_lon=117.0, lon_step=0.01000213623046875,
        lat_count=201, lon_count=201,
    )
    array = response.to_xarray()
    np.testing.assert_array_equal(array.latitude, np.linspace(41, 39, 201))
    np.testing.assert_array_equal(array.longitude, np.linspace(115, 117, 201))
    np.testing.assert_array_equal(array.values, response.data)
    assert response.lon_step == 0.01000213623046875


def test_explicit_coordinates_and_materially_different_steps_are_preserved():
    response = GridArray2D(
        data=np.zeros((2, 3)),
        start_lat=41, end_lat=39, lat_step=-1, lat_count=2,
        start_lon=115, end_lon=117, lon_step=0.5, lon_count=3,
    )
    array = response.to_xarray()
    np.testing.assert_array_equal(array.latitude, [41, 40])
    np.testing.assert_array_equal(array.longitude, [115, 115.5, 116])
    response.lats, response.lons = [41, 39], [115, 116.2, 117]
    array = response.to_xarray()
    np.testing.assert_array_equal(array.longitude, response.lons)


def test_grid_scalar2d_rejects_data_length_mismatch():
    with pytest.raises(ValueError, match="GridScalar2D data length"):
        GridScalar2D.create_from_protobuf(
            make_grid_scalar2d_content(data=[1.0] * 5)
        )


def test_grid_scalar2d_rejects_coordinate_length_mismatch():
    with pytest.raises(ValueError, match="longitude coordinate length"):
        GridScalar2D.create_from_protobuf(
            make_grid_scalar2d_content(lons=[110.0, 111.0])
        )


@pytest.mark.parametrize("field", ["u_data", "v_data"])
def test_grid_vector2d_rejects_component_length_mismatch(field):
    kwargs = {field: [1.0] * 5}
    with pytest.raises(ValueError, match="GridVector2D"):
        GridVector2D.create_from_protobuf(
            make_grid_vector2d_content(**kwargs)
        )


def test_grid_vector2d_rejects_coordinate_length_mismatch():
    with pytest.raises(ValueError, match="latitude coordinate length"):
        GridVector2D.create_from_protobuf(
            make_grid_vector2d_content(lats=[30.0])
        )
