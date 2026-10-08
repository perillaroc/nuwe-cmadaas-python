"""The cataloged NAFP latest-time API returns a table, not a file list."""

import pandas as pd
import pytest

from tests.integration.case_registry import case_parameters, resolve_case_value


@pytest.mark.parametrize("case", case_parameters("model_file_latest"))
def test_registered_case(case, request, integration_profile, dataset_profile):
    case_id = case["case_id"]
    if not case["enabled"] or not integration_profile.get("cases", {}).get(case_id, {}).get("enabled", False):
        pytest.skip(f"Case capability is disabled: {case_id}")

    dataset = dataset_profile(case["profile_key"])
    kwargs = resolve_case_value(case["public_kwargs"], dataset, request)
    response = request.getfixturevalue("real_client").callAPI_to_array2D(**kwargs)

    assert response.ok, (
        f"{case['interface_id']}: {response.request.error_code} "
        f"{response.request.error_message}"
    )
    table = response.to_pandas()
    expected = case["expected_return_contract"]
    assert expected["kind"] == "dataframe"
    assert not table.empty
    assert 0 < len(table) <= expected["max_rows"]
    assert list(table.columns) == expected["columns"]
    latest = pd.to_datetime(table["Datetime"], format="%Y%m%d%H%M%S", errors="raise")
    now = pd.Timestamp.now()
    assert latest.le(now).all()
    assert latest.ge(now - pd.Timedelta(hours=int(dataset["latest_hours"]))).all()
