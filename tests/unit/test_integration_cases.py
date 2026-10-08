"""Guard the static case inventory against registry drift."""

from pathlib import Path
from importlib import import_module

import pytest
import yaml

import nuwe_cmadaas
from nuwe_cmadaas.interfaces import INTERFACE_SPECS
from nuwe_cmadaas.music import CMADaaSClient
from tests.integration import case_registry
from tests.integration.case_registry import load_cases


def _profile_references(value):
    if isinstance(value, dict):
        if set(value) == {"profile"}:
            return {value["profile"]}
        return set().union(*(_profile_references(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_profile_references(item) for item in value))
    return set()


def test_case_manifest_maps_every_registered_high_level_combination():
    cases = load_cases()
    by_id = {case["case_id"]: case for case in cases}
    assert len(cases) == len(by_id)
    project_root = Path(__file__).resolve().parents[2]
    example = yaml.safe_load(
        (project_root / "tests/integration/profiles.example.yaml").read_text(encoding="utf-8")
    )
    assert set(example["cases"]) == set(by_id), "Example profile lacks a case toggle"

    spec_keys = [(spec.family, tuple(sorted(spec.query_features))) for spec in INTERFACE_SPECS]
    assert len(spec_keys) == len(set(spec_keys)), "Duplicate production registry key"
    expected = dict(zip(spec_keys, INTERFACE_SPECS))
    registered_families = {spec.family for spec in INTERFACE_SPECS}
    high_level_cases = [case for case in cases if case["family"] in registered_families]
    actual_keys = {(case["family"], tuple(case["query_features"])) for case in high_level_cases}
    assert actual_keys == set(expected), "Missing or unregistered high-level case combination"

    public_functions = {
        "retrieve_obs_station", "retrieve_obs_grid", "retrieve_obs_upper_air",
        "download_obs_file", "download_obs_upper_air_file", "retrieve_model_grid",
        "retrieve_model_point", "download_model_file",
    }
    assert {case["public_function"] for case in high_level_cases
            if not case["public_function"].startswith("CMADaaSClient.")} == public_functions
    assert all(callable(getattr(nuwe_cmadaas, name)) for name in public_functions)
    for case in high_level_cases:
        key = (case["family"], tuple(case["query_features"]))
        spec = expected[key]
        assert case["interface_id"] == spec.interface_id, case["case_id"]
        if spec.return_type != "file_list":
            assert case["public_function"] != "download_obs_file", case["case_id"]
            assert case["public_function"] != "download_model_file", case["case_id"]

    low_level_cases = [case for case in cases if case["family"].startswith("music_")]
    methods = {name for name in vars(CMADaaSClient) if name.startswith("callAPI_to_")}
    assert len(methods) == 9
    assert {case["public_function"] for case in low_level_cases} == {
        f"CMADaaSClient.{name}" for name in methods
    }
    assert len({case["family"] for case in low_level_cases}) == 9
    for case in low_level_cases:
        method = case["public_function"].split(".", 1)[1]
        assert case["profile_key"] == method
        assert case["public_kwargs"]["interface_id"] == case["interface_id"]

    for case in cases:
        assert case["query_features"] == sorted(set(case["query_features"]))
        assert case["documentation_anchor"]
        assert case["implemented"], case["case_id"]
        assert case["profile_key"]
        assert case["public_kwargs"]
        assert case["expected_return_contract"]
        assert case["test_node"]
        path, node = case["test_node"].split("::", 1)
        assert path.startswith("tests/integration/")
        assert node.endswith(f"[{case['case_id']}]")
        assert (project_root / path).is_file()
        module = import_module(path.removesuffix(".py").replace("/", "."))
        assert callable(getattr(module, node.split("[", 1)[0]))
        profile_group = "low_level" if case["family"].startswith("music_") else "datasets"
        assert case["profile_key"] in example[profile_group]
        profile = example[profile_group][case["profile_key"]]
        assert _profile_references(case["public_kwargs"]) <= profile.keys()
        assert _profile_references(case["expected_return_contract"]) <= profile.keys()
        assert case["online_status"] in {"implemented-unverified", "passed", "failed"}
        assert case["reason"]
        if case["online_status"] == "passed":
            assert case["last_verified_environment_and_time"]
        if not case["enabled"]:
            assert case["online_status"] != "passed", case["case_id"]


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
