import inspect
from pathlib import Path

import pandas as pd
import pytest

import nuwe_cmadaas
from nuwe_cmadaas import model, music, obs
from nuwe_cmadaas.model import retrieve_model_grid
from nuwe_cmadaas.obs import retrieve_obs_grid
from tests.fixtures import FakeCMADaaSClient, make_grid_array2d_response


pytestmark = pytest.mark.unit


def test_public_namespaces_expose_only_declared_stable_symbols():
    expected = {
        "music": {
            "Array2D", "DataBlock", "FileInfo", "FilesInfo", "GridArray2D",
            "GridScalar2D", "GridVector2D", "MusicError", "CMADaaSClient",
            "CMADaaSError", "CMADaaSAuthenticationError",
            "CMADaaSConfigurationError", "CMADaaSDecodeError",
            "CMADaaSDownloadError", "CMADaaSQueryError", "CMADaaSRequestError",
            "CMADaaSTransportError", "CMADaasConfig", "load_cmadaas_config",
            "create_client", "get_or_create_client",
        },
        "model": {"retrieve_model_grid", "retrieve_model_point", "download_model_file"},
        "obs": {
            "retrieve_obs_station", "retrieve_obs_grid", "retrieve_obs_upper_air",
            "download_obs_file", "download_obs_upper_air_file",
        },
    }

    for namespace_name, names in expected.items():
        namespace = {"music": music, "model": model, "obs": obs}[namespace_name]
        assert set(namespace.__all__) == names
        assert all(hasattr(namespace, name) for name in names)

    assert set(nuwe_cmadaas.__all__) >= {
        "CMADaaSClient", "retrieve_model_grid", "retrieve_obs_grid",
        "download_model_file", "download_obs_file",
    }


def test_package_declares_pep561_type_information():
    marker = Path(nuwe_cmadaas.__file__).with_name("py.typed")

    assert marker.exists()


def test_reference_docs_cover_all_high_level_functions():
    docs_root = Path(__file__).parents[1] / ".." / "docs" / "source"
    reference = (docs_root / "reference.rst").resolve().read_text(encoding="utf-8")
    matrix = (docs_root / "guide" / "support-matrix.rst").resolve().read_text(encoding="utf-8")

    for function_name in (
            "retrieve_model_grid", "retrieve_model_point", "download_model_file",
            "retrieve_obs_station", "retrieve_obs_grid", "retrieve_obs_upper_air",
            "download_obs_file", "download_obs_upper_air_file",
    ):
        assert f".. autofunction:: {function_name}" in reference
    assert "查询组合" in matrix
    assert "返回类型" in matrix


def test_documented_high_level_signature_can_be_constructed_offline():
    assert "strict" in inspect.signature(retrieve_model_grid).parameters
    assert "strict" in inspect.signature(retrieve_obs_grid).parameters

    client = FakeCMADaaSClient(make_grid_array2d_response())
    result = retrieve_obs_grid(
        "SYNTHETIC_GRID",
        parameter="TEM",
        time=pd.Timestamp("2026-01-02"),
        client=client,
    )

    assert result.name == "synthetic_temperature"
    assert result.attrs["units"] == "K"
    assert client.calls[0][0] == "getSurfEleGridByTime"
