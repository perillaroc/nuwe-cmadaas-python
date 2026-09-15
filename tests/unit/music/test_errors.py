from pathlib import Path

import pandas as pd
import pytest

from nuwe_cmadaas.interfaces import UnsupportedQueryError
from nuwe_cmadaas.model import download_model_file, retrieve_model_grid, retrieve_model_point
from nuwe_cmadaas.music import (
    CMADaaSAuthenticationError,
    CMADaaSError,
    CMADaaSQueryError,
    CMADaaSRequestError,
    MusicError,
)
from nuwe_cmadaas.obs import download_obs_file, retrieve_obs_grid, retrieve_obs_station, retrieve_obs_upper_air
from tests.fixtures import (
    FakeCMADaaSClient,
    make_array2d_response,
    make_files_info_response,
    make_grid_array2d_response,
)


pytestmark = pytest.mark.unit


def test_response_exposes_ok_and_raises_typed_authentication_error():
    response = make_array2d_response(
        error_code=-1004,
        error_message="Synthetic authentication failure",
    )

    assert response.ok is False
    with pytest.raises(CMADaaSAuthenticationError) as raised:
        response.raise_for_error(
            interface_id="syntheticInterface",
            params={"userId": "synthetic-user", "pwd": "synthetic-password"},
        )

    error = raised.value
    assert isinstance(error, CMADaaSError)
    assert error.error_code == -1004
    assert error.server_message == "Synthetic authentication failure"
    assert error.interface_id == "syntheticInterface"
    assert error.params["pwd"] == "<redacted>"
    assert "synthetic-password" not in str(error)


def test_successful_response_raise_for_error_is_a_no_op():
    response = make_array2d_response()

    assert response.ok is True
    assert response.raise_for_error() is response


def test_unsupported_query_error_is_in_query_error_hierarchy():
    assert issubclass(UnsupportedQueryError, CMADaaSQueryError)


def test_strict_model_grid_raises_structured_request_error():
    client = FakeCMADaaSClient(
        make_grid_array2d_response(
            error_code=-3234,
            error_message="Synthetic model query failure",
        )
    )

    with pytest.raises(CMADaaSRequestError) as raised:
        retrieve_model_grid(
            "SYNTHETIC_MODEL",
            parameter="TEM",
            client=client,
            strict=True,
        )

    assert raised.value.error_code == -3234
    assert raised.value.interface_id == "getNafpEleGrid"
    assert client.calls[0][0] == "getNafpEleGrid"


@pytest.mark.parametrize(
    ("call", "result", "expected_interface"),
    [
        (
            lambda client: retrieve_model_point(
                "SYNTHETIC_MODEL", "TEM", pd.Timestamp("2026-01-02"), "24h",
                level_type=100, level=850, point=(30.0, 110.0), client=client,
                strict=True,
            ),
            make_array2d_response(error_code=-3001, error_message="point failure"),
            "getNafpEleAtPointByTimeAndLevelAndValidtime",
        ),
        (
            lambda client: retrieve_obs_station(
                "SYNTHETIC_STATION", elements="TEM", time=pd.Timestamp("2026-01-02"),
                client=client, strict=True,
            ),
            make_array2d_response(error_code=-3002, error_message="station failure"),
            "getSurfEleByTime",
        ),
        (
            lambda client: retrieve_obs_grid(
                "SYNTHETIC_GRID", parameter="TEM", time=pd.Timestamp("2026-01-02"),
                client=client, strict=True,
            ),
            make_grid_array2d_response(error_code=-3003, error_message="grid failure"),
            "getSurfEleGridByTime",
        ),
        (
            lambda client: retrieve_obs_upper_air(
                elements="TEM", time=pd.Timestamp("2026-01-02"), client=client,
                strict=True,
            ),
            make_array2d_response(error_code=-3004, error_message="upper-air failure"),
            "getUparEleByTime",
        ),
    ],
)
def test_strict_retrievals_raise_with_interface_context(call, result, expected_interface):
    client = FakeCMADaaSClient(result)

    with pytest.raises(CMADaaSRequestError) as raised:
        call(client)

    assert raised.value.interface_id == expected_interface


def test_strict_file_downloads_raise_and_legacy_path_warns(tmp_path):
    error_result = make_files_info_response(
        error_code=-3005,
        error_message="file failure",
    )
    strict_client = FakeCMADaaSClient(error_result)

    with pytest.raises(CMADaaSRequestError) as raised:
        download_model_file("SYNTHETIC_MODEL", output_dir=tmp_path, client=strict_client, strict=True)

    assert raised.value.interface_id == "getNafpFile"

    legacy_client = FakeCMADaaSClient(error_result)
    with pytest.warns(DeprecationWarning, match="MusicError"):
        result = download_obs_file("SYNTHETIC_STATION", output_dir=Path(tmp_path), client=legacy_client)
    assert result == MusicError(-3005, "file failure")
