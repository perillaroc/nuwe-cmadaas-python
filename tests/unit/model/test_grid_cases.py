"""Cataloged model-grid cases and removed combinations stay in sync."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface
from nuwe_cmadaas.model import retrieve_model_grid
from tests.fixtures import FakeCMADaaSClient, make_grid_array2d_response
from tests.integration.case_registry import load_cases, resolve_case_value


pytestmark = pytest.mark.unit
PROFILE = yaml.safe_load(
    (Path(__file__).resolve().parents[2] / "integration/profiles.example.yaml")
    .read_text(encoding="utf-8")
)
BASE_TIME = (pd.Timestamp.now() - pd.offsets.Day()).normalize() - pd.Timedelta(days=2)
MODEL_CYCLE_TIME = BASE_TIME + pd.Timedelta(hours=6)
RECTANGLE = {
    "type": "rect", "start_longitude": 115.0, "end_longitude": 117.0,
    "start_latitude": 41.0, "end_latitude": 39.0,
}


class SyntheticRequest:
    def getfixturevalue(self, name):
        return {
            "base_time": BASE_TIME,
            "model_cycle_time": MODEL_CYCLE_TIME,
            "start_time_for_reps": MODEL_CYCLE_TIME,
        }[name]


@pytest.mark.parametrize(
    "case",
    load_cases("model_grid_forecast") + load_cases("model_grid_analysis"),
    ids=lambda case: case["case_id"],
)
def test_model_grid_case_reaches_declared_interface(case):
    dataset = PROFILE["datasets"][case["profile_key"]]
    kwargs = resolve_case_value(case["public_kwargs"], dataset, SyntheticRequest())
    client = FakeCMADaaSClient(make_grid_array2d_response())

    retrieve_model_grid(**kwargs, client=client)

    assert len(client.calls) == 1
    interface_id, params = client.calls[0]
    assert interface_id == case["interface_id"]
    assert params["dataCode"] == dataset["data_code"]
    assert params["fcstEle"] == dataset["parameter"]
    assert params["time"] == kwargs["start_time"].strftime("%Y%m%d%H%M%S")
    features = set(case["query_features"])
    assert ("levelType" in params) == ("level" in features)
    assert ("fcstLevel" in params) == ("level" in features)
    assert ("validTime" in params) == ("valid_time" in features)
    assert ("fcstMember" in params) == ("number" in features)
    assert ("minLat" in params) == ("region" in features)
    if "level" in features:
        assert params["levelType"] == str(kwargs["level_type"])
        assert params["fcstLevel"] == str(kwargs["level"])
    if "valid_time" in features:
        assert params["validTime"] == "24"
    if "number" in features:
        assert params["fcstMember"] == kwargs["number"]
    if "region" in features:
        assert {key for key in ("minLat", "minLon", "maxLat", "maxLon")} <= params.keys()


ALL_GRID_FEATURES = [
    (), ("time",), ("level",), ("valid_time",),
    ("level", "time"), ("time", "valid_time"), ("level", "valid_time"),
    ("level", "time", "valid_time"),
    ("region",), ("region", "time"), ("level", "region"),
    ("region", "valid_time"), ("level", "region", "time"),
    ("region", "time", "valid_time"), ("level", "region", "valid_time"),
    ("level", "region", "time", "valid_time"),
    ("level", "number", "time", "valid_time"),
    ("level", "number", "region", "time", "valid_time"),
]
CATALOG_FEATURES = {
    "forecast": {
        frozenset(("time",)),
        frozenset(("level", "time", "valid_time")),
        frozenset(("region", "time")),
        frozenset(("level", "region", "time", "valid_time")),
        frozenset(("level", "number", "time", "valid_time")),
        frozenset(("level", "number", "region", "time", "valid_time")),
    },
    "analysis": {
        frozenset(("level", "time")),
        frozenset(("level", "region", "time")),
    },
}
REMOVED = [
    (data_type, features)
    for data_type, catalog_features in CATALOG_FEATURES.items()
    for features in ALL_GRID_FEATURES
    if frozenset(features) not in catalog_features
]
assert len(REMOVED) == 28


@pytest.mark.parametrize(("data_type", "features"), REMOVED)
def test_catalog_absent_model_grid_combination_rejects_before_request(data_type, features):
    kwargs = {"data_type": data_type}
    if "time" in features:
        kwargs["start_time"] = BASE_TIME
    if "level" in features:
        kwargs.update(level_type=100, level=850)
    if "valid_time" in features:
        kwargs["forecast_time"] = "24h"
    if "region" in features:
        kwargs["region"] = RECTANGLE
    if "number" in features:
        kwargs["number"] = 0
    client = FakeCMADaaSClient(make_grid_array2d_response())

    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        resolve_interface(f"model_grid_{data_type}", features)
    with pytest.raises(UnsupportedQueryError, match="unsupported query features"):
        retrieve_model_grid(
            "SYNTHETIC_MODEL", parameter="TEM", client=client, **kwargs
        )

    assert client.calls == []
