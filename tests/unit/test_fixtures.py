import numpy as np
import pytest

from tests.fixtures import (
    FakeCMADaaSClient,
    make_array2d_response,
    make_grid_array2d_response,
)


pytestmark = pytest.mark.unit


def test_synthetic_array2d_fixture_is_deterministic():
    result = make_array2d_response()

    assert result.request.error_code == 0
    assert result.element_names == ["Station_Id_C", "Lat", "Lon", "TEM"]
    assert result.data.tolist() == [
        ["FAKE001", "30.0", "110.0", "280.0"],
        ["FAKE002", "31.0", "111.0", "281.5"],
    ]


def test_synthetic_grid_fixture_preserves_dimensions_and_metadata():
    result = make_grid_array2d_response()
    field = result.to_xarray()

    assert field.name == "synthetic_temperature"
    assert field.attrs["units"] == "K"
    assert field.dims == ("latitude", "longitude")
    np.testing.assert_array_equal(field.latitude, [30.0, 31.0])
    np.testing.assert_array_equal(field.longitude, [110.0, 111.0, 112.0])
    np.testing.assert_array_equal(
        field.values,
        [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]],
    )


def test_fake_client_records_interface_and_parameters(fake_client):
    params = {"dataCode": "SYNTHETIC_DATA", "times": "20260102000000"}

    result = fake_client.callAPI_to_array2D("syntheticInterface", params)

    assert result is fake_client.result
    assert fake_client.calls == [("syntheticInterface", params)]
    assert isinstance(fake_client, FakeCMADaaSClient)
