"""Guard the static case inventory against registry drift."""

from pathlib import Path

import pytest
import yaml

from nuwe_cmadaas.interfaces import INTERFACE_SPECS
from tests.integration import case_registry
from tests.integration.case_registry import load_cases


def test_case_manifest_maps_every_registered_high_level_combination():
    cases = load_cases()
    by_id = {case["case_id"]: case for case in cases}
    assert len(cases) == len(by_id)

    expected = {
        (spec.family, tuple(sorted(spec.query_features))): spec.interface_id
        for spec in INTERFACE_SPECS
    }
    actual = {
        (case["family"], tuple(case["query_features"])): case["interface_id"]
        for case in cases
    }
    assert len(actual) == len(expected)
    assert actual == expected
    for case in cases:
        key = (case["family"], tuple(case["query_features"]))
        assert case["interface_id"] == expected[key]

    for case in cases:
        assert case["documentation_anchor"]
        if case["implemented"]:
            assert case["profile_key"]
            assert case["public_kwargs"]
            assert case["expected_return_contract"]
            assert case["test_node"]
            project_root = Path(__file__).resolve().parents[2]
            assert (project_root / case["test_node"].split("::", 1)[0]).is_file()
            assert case["online_status"] in {
                "implemented-unverified", "passed", "skipped", "failed", "blocked-contract"
            }
        elif case["online_status"] == "unsupported":
            assert not case["enabled"]
            assert case["test_node"] is None


def test_load_cases_discovers_nested_manifests_and_filters(monkeypatch, tmp_path):
    for directory, records in {
        "obs/station": [
            {"case_id": "STATION", "family": "station", "implemented": True},
            {"case_id": "PLANNED", "family": "station", "implemented": False},
        ],
        "model/grid": [{"case_id": "GRID", "family": "grid", "implemented": True}],
    }.items():
        folder = tmp_path / directory
        folder.mkdir(parents=True)
        (folder / "cases.yaml").write_text(yaml.safe_dump({"cases": records}))
    monkeypatch.setattr(case_registry, "CASES_ROOT", tmp_path)

    assert [case["case_id"] for case in load_cases()] == ["GRID", "STATION", "PLANNED"]
    assert [case["case_id"] for case in load_cases("station", implemented_only=True)] == [
        "STATION"
    ]


def test_load_cases_rejects_duplicate_ids_before_filtering(monkeypatch, tmp_path):
    for directory, family in [("obs/station", "station"), ("model/grid", "grid")]:
        folder = tmp_path / directory
        folder.mkdir(parents=True)
        record = {"case_id": "DUPLICATE", "family": family, "implemented": True}
        (folder / "cases.yaml").write_text(yaml.safe_dump({"cases": [record]}))
    monkeypatch.setattr(case_registry, "CASES_ROOT", tmp_path)

    with pytest.raises(ValueError, match="Duplicate case_id") as exc:
        load_cases("station")
    assert "obs/station/cases.yaml" in str(exc.value)
    assert "model/grid/cases.yaml" in str(exc.value)
