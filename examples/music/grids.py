"""Offline native grid responses shared with the executable grid guide.

From the repository root: ``python -m examples.music.grids``.
Synthetic protobuf travels through the real MUSIC client and xarray converters.
"""

import numpy as np
import xarray as xr

from examples._support import (
    SyntheticTransport,
    make_grid_array2d_content,
    make_grid_scalar2d_content,
    make_grid_vector2d_content,
    make_synthetic_music_client,
)
from nuwe_cmadaas.music import (
    CMADaaSDecodeError,
    CMADaaSRequestError,
    GridArray2D,
    GridScalar2D,
    GridVector2D,
)


def make_grid_client():
    """Register all three grid formats, empty/error responses and a bad vector."""
    transport = SyntheticTransport()
    scalar_id = "getNafpEleGridInRectByTimeAndLevelAndValidtime"
    vector_id = "getNafpVectorEleGridByTimeAndLevelAndValidtime"
    scalar_params = {
        "dataCode": "SYNTHETIC_GRID", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "minLat": "30.0", "maxLat": "31.0",
        "minLon": "110.0", "maxLon": "112.0",
    }
    vector_params = {
        "dataCode": "SYNTHETIC_VECTOR", "fcstuele": "synthetic_u_wind",
        "fcstvele": "synthetic_v_wind", "time": "20260102060000",
        "levelType": "100", "fcstLevel": "850", "validTime": "0",
    }
    for method, interface_id, params, factory in [
        ("callAPI_to_gridArray2D", scalar_id, scalar_params, make_grid_array2d_content),
        ("callAPI_to_gridScalar2D", scalar_id, scalar_params, make_grid_scalar2d_content),
        ("callAPI_to_gridVector2D", vector_id, vector_params, make_grid_vector2d_content),
    ]:
        transport.register_api(method, interface_id, params, factory())
        empty = {"lats": [], "lons": [], "lat_count": 0, "lon_count": 0}
        if method == "callAPI_to_gridVector2D":
            empty.update(u_data=[], v_data=[])
        else:
            empty["data"] = []
        transport.register_api(
            method, interface_id, {**params, "dataCode": "SYNTHETIC_EMPTY"}, factory(**empty),
        )
        transport.register_api(
            method, interface_id, {**params, "dataCode": "SYNTHETIC_ERROR"},
            factory(error_code=-7234, error_message="Synthetic grid service failure"),
        )
    transport.register_api(
        "callAPI_to_gridVector2D", vector_id,
        {**vector_params, "dataCode": "SYNTHETIC_MALFORMED"},
        make_grid_vector2d_content(v_data=[-1, -2, -3, -4, -5]),
    )
    return make_synthetic_music_client(transport), transport


def check_results(responses, fields, transport, scalar_params, vector_params):
    """Check independent coordinates, values, names, attrs and failure contracts."""
    scalar_id = "getNafpEleGridInRectByTimeAndLevelAndValidtime"
    vector_id = "getNafpVectorEleGridByTimeAndLevelAndValidtime"
    assert scalar_params == {
        "dataCode": "SYNTHETIC_GRID", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "minLat": "30.0", "maxLat": "31.0",
        "minLon": "110.0", "maxLon": "112.0",
    }
    assert vector_params == {
        "dataCode": "SYNTHETIC_VECTOR", "fcstuele": "synthetic_u_wind",
        "fcstvele": "synthetic_v_wind", "time": "20260102060000",
        "levelType": "100", "fcstLevel": "850", "validTime": "0",
    }
    kinds = {"array": GridArray2D, "scalar": GridScalar2D, "vector": GridVector2D}
    assert set(responses) == {
        *kinds, *(f"empty_{name}" for name in kinds),
        *(f"failed_{name}" for name in kinds), "malformed_vector",
    }
    assert set(fields) == {*kinds, *(f"empty_{name}" for name in kinds)}
    for name, response_type in kinds.items():
        vector = name == "vector"
        interface_id = vector_id if vector else scalar_id
        params = vector_params if vector else scalar_params
        metadata = {
            "interface_id": interface_id, "time": "20260102060000",
            "level_type": "100" if vector else "103",
            "level": "850" if vector else "2", "valid_time": "0" if vector else "24",
        }
        attrs = {**metadata, "request_time": "20260102000000", "response_time": "20260102000001"}
        if not vector:
            attrs["units"] = "K"
        for prefix, shape in [("", (2, 3)), ("empty_", (0, 0))]:
            key = prefix + name
            response, field = responses[key], fields[key]
            assert isinstance(response, response_type) and response.ok
            assert response.request.error_code == 0 and response.request.cause is None
            assert response.raise_for_error(interface_id=interface_id, params=params) is response
            assert (response.lat_count, response.lon_count) == shape
            assert (response.request.row_count, response.request.col_count) == shape
            assert response.metadata == metadata and field.attrs == attrs
            assert tuple(field.sizes) == ("latitude", "longitude")
            assert tuple(field.sizes.values()) == shape
            assert set(field.coords) == {"latitude", "longitude"}
            assert field.latitude.values.tolist() == ([30.0, 31.0] if not prefix else [])
            assert field.longitude.values.tolist() == ([110.0, 111.0, 112.0] if not prefix else [])
            assert response.lats == field.latitude.values.tolist()
            assert response.lons == field.longitude.values.tolist()
            assert field.latitude.attrs == {"units": "degrees_north", "standard_name": "latitude", "long_name": "latitude"}
            assert field.longitude.attrs == {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude"}
            if vector:
                assert isinstance(field, xr.Dataset)
                assert list(field.data_vars) == ["synthetic_u_wind", "synthetic_v_wind"]
                for component, raw, expected in [
                    ("synthetic_u_wind", response.u_datas, [[1, 2, 3], [4, 5, 6]]),
                    ("synthetic_v_wind", response.v_datas, [[-1, -2, -3], [-4, -5, -6]]),
                ]:
                    variable = field[component]
                    assert variable.dims == ("latitude", "longitude") and variable.shape == shape
                    assert np.issubdtype(variable.dtype, np.floating) and variable.attrs == {}
                    np.testing.assert_array_equal(variable.values, raw)
                    np.testing.assert_array_equal(variable.values, np.empty(shape) if prefix else expected)
            else:
                assert isinstance(field, xr.DataArray)
                assert field.dims == ("latitude", "longitude") and field.shape == shape
                assert np.issubdtype(field.dtype, np.floating)
                assert field.name == response.user_element_name == "synthetic_temperature"
                assert response.units == "K"
                np.testing.assert_array_equal(field.values, response.data)
                np.testing.assert_array_equal(
                    field.values, np.empty(shape) if prefix else [[280, 280.5, 281], [281.5, 282, 282.5]],
                )
        failed = responses[f"failed_{name}"]
        assert isinstance(failed, response_type) and not failed.ok
        assert (failed.lat_count, failed.lon_count) == (0, 0)
        assert failed.lats == failed.lons == []
        if vector:
            assert failed.u_datas.shape == failed.v_datas.shape == (0, 0)
        else:
            assert failed.data.shape == (0, 0)
        try:
            failed.raise_for_error(interface_id=interface_id, params={**params, "dataCode": "SYNTHETIC_ERROR"})
        except CMADaaSRequestError as error:
            assert error.error_code == -7234 and error.interface_id == interface_id
            assert error.params == {**params, "dataCode": "SYNTHETIC_ERROR"}
        else:
            raise AssertionError("service failure must raise with context")
        try:
            failed.to_xarray()
        except CMADaaSRequestError as error:
            assert error.error_code == -7234 and error.interface_id is None
        else:
            raise AssertionError("failed grids must not convert to successful empty fields")
    malformed = responses["malformed_vector"]
    assert not malformed.ok and malformed.request.error_code == -10003
    try:
        malformed.raise_for_error(interface_id=vector_id, params={**vector_params, "dataCode": "SYNTHETIC_MALFORMED"})
    except CMADaaSDecodeError as error:
        assert error.error_code == -10003 and error.interface_id == vector_id
        assert isinstance(error.cause, ValueError) and error.__cause__ is error.cause
    else:
        raise AssertionError("vector component length mismatch must fail decoding")
    try:
        malformed.to_xarray()
    except CMADaaSDecodeError:
        pass
    else:
        raise AssertionError("bad vector must not convert")
    assert fields["array"].sel(latitude=30.0, longitude=111.0).item() == 280.5
    assert fields["vector"]["synthetic_v_wind"].sel(latitude=31.0, longitude=112.0).item() == -6.0
    assert len(transport.calls) == len(transport.responses) == 10
    assert all(response.closed and not response.streamed for response in transport.responses)


def run_example():
    """Execute all native methods and conversions without configuration or credentials."""
    client, transport = make_grid_client()
    scalar_id = "getNafpEleGridInRectByTimeAndLevelAndValidtime"
    vector_id = "getNafpVectorEleGridByTimeAndLevelAndValidtime"
    scalar_params = {
        "dataCode": "SYNTHETIC_GRID", "fcstEle": "synthetic_temperature",
        "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
        "validTime": "24", "minLat": "30.0", "maxLat": "31.0",
        "minLon": "110.0", "maxLon": "112.0",
    }
    vector_params = {
        "dataCode": "SYNTHETIC_VECTOR", "fcstuele": "synthetic_u_wind",
        "fcstvele": "synthetic_v_wind", "time": "20260102060000",
        "levelType": "100", "fcstLevel": "850", "validTime": "0",
    }
    responses, fields = {}, {}
    for name, method, interface_id, params in [
        ("array", client.callAPI_to_gridArray2D, scalar_id, scalar_params),
        ("scalar", client.callAPI_to_gridScalar2D, scalar_id, scalar_params),
        ("vector", client.callAPI_to_gridVector2D, vector_id, vector_params),
    ]:
        for prefix, code in [("", params["dataCode"]), ("empty_", "SYNTHETIC_EMPTY"),
                             ("failed_", "SYNTHETIC_ERROR")]:
            query = {**params, "dataCode": code}
            key = prefix + name
            responses[key] = method(interface_id, query)
            assert query == {**params, "dataCode": code}
            if prefix != "failed_":
                responses[key].raise_for_error(interface_id=interface_id, params=query)
                fields[key] = responses[key].to_xarray()
    responses["malformed_vector"] = client.callAPI_to_gridVector2D(
        vector_id, {**vector_params, "dataCode": "SYNTHETIC_MALFORMED"},
    )
    check_results(responses, fields, transport, scalar_params, vector_params)
    return responses, fields


if __name__ == "__main__":
    responses, fields = run_example()
    for name in ["array", "scalar", "vector"]:
        print(f"\n{name}: {type(responses[name]).__name__}, ok={responses[name].ok}")
        print(fields[name])
        print(f"attrs: {fields[name].attrs}")
    for name in ["empty_array", "empty_scalar", "empty_vector"]:
        print(f"{name}: ok={responses[name].ok}, sizes={dict(fields[name].sizes)}")
    for name in ["failed_array", "failed_scalar", "failed_vector", "malformed_vector"]:
        print(f"{name}: ok={responses[name].ok}, code={responses[name].request.error_code}")
    print("\nAll synthetic native grid contracts passed.")
