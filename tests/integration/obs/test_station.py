"""Manifest-backed station cases; B04 will add the remaining combinations."""

import pandas as pd
import pytest

from nuwe_cmadaas.obs import retrieve_obs_station

from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("obs_station"))
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    kwargs["client"] = request.getfixturevalue("real_client")
    kwargs["strict"] = True
    table = retrieve_obs_station(**kwargs)

    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataframe"
    assert isinstance(table, pd.DataFrame)
    if expected["nonempty"]:
        assert not table.empty
    columns = resolve_case_value(expected["columns"], dataset, request)
    assert set(columns).issubset(table.columns)
    station_id = resolve_case_value(expected["station_matches"], dataset, request)
    assert table["Station_Id_C"].astype(str).eq(str(station_id)).all()
