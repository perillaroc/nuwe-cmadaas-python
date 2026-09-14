import numpy as np
import pytest

from nuwe_cmadaas.music.data import (
    Array2D,
    DataBlock,
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


pytestmark = pytest.mark.unit


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
            make_grid_array2d_content(lat_count=2, lon_count=4)
        )
