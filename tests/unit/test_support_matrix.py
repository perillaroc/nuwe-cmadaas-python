"""Guard generated documentation against case and registry drift."""

from dataclasses import replace
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from nuwe_cmadaas.interfaces import INTERFACE_SPECS
from tests.integration.case_registry import load_cases


pytest.importorskip("sphinx", reason="Generated references require the docs dependency group")
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("support_matrix", ROOT / "docs/_ext/support_matrix.py")
matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matrix)
pytestmark = pytest.mark.unit


@pytest.fixture
def inventory(tmp_path):
    case = next(c for c in load_cases() if c["family"] == "obs_grid")
    registry = next(s for s in INTERFACE_SPECS if s.family == case["family"]
                    and sorted(s.query_features) == case["query_features"])
    guide = tmp_path / "docs/source" / (case["documentation_anchor"].split("#")[0] + ".md")
    guide.parent.mkdir(parents=True)
    guide.write_text("# Guide\n\n```{cmadaas-case-index}\n```\n")
    test = tmp_path / case["test_node"].split("::")[0]
    test.parent.mkdir(parents=True)
    test.write_text("def test_registered_case():\n    pass\n")
    manifest = test.parent / "cases.yaml"
    manifest.write_text(yaml.safe_dump({"cases": [case]}))
    return tmp_path, manifest, case, registry, guide, test


def test_generated_inventory_matches_the_test_loader_and_covers_public_methods():
    cases = matrix.load_inventory(ROOT)
    assert {c["case_id"] for c in cases} == {c["case_id"] for c in load_cases()}
    for case in cases:
        assert "```{cmadaas-case-index}" in (
            ROOT / "docs/source" / (case["documentation_anchor"].split("#")[0] + ".md")
        ).read_text()
    rendered = "\n".join(matrix.render_matrix(cases))
    for case in cases:
        assert f".. _{matrix.case_label(case)}:" in rendered
        assert case["test_node"] in rendered
        assert case["documentation_anchor"] in rendered


@pytest.mark.parametrize("field,value,message", [
    ("interface_id", "missingInterface", "mismatched interface"),
    ("test_node", "tests/integration/missing.py::test_registered_case[OG-002]", "Invalid test node"),
    ("online_status", "skipped", "Invalid verification status"),
    ("last_verified_environment_and_time", None, "Missing historical verification context"),
    ("public_function", "missing_public_function", "Unknown public entry"),
    ("expected_return_contract", {"kind": "unknown"}, "Unknown return contract"),
    ("implemented", "true", "Invalid implemented flag"),
])
def test_invalid_case_evidence_fails_generation(inventory, field, value, message):
    root, manifest, case, registry, _, _ = inventory
    case[field] = value
    manifest.write_text(yaml.safe_dump({"cases": [case]}))
    with pytest.raises(ValueError, match=message):
        matrix.load_inventory(root, (registry,))


def test_missing_registry_combination_fails_generation(inventory):
    root, _, _, registry, _, _ = inventory
    extra = replace(registry, query_features=frozenset({"not-covered"}))
    with pytest.raises(ValueError, match="Missing registered combinations"):
        matrix.load_inventory(root, (registry, extra))


def test_duplicate_ids_in_new_nested_manifest_fail_generation(inventory):
    root, manifest, _, registry, _, _ = inventory
    nested = manifest.parent / "new-category/cases.yaml"
    nested.parent.mkdir()
    nested.write_text(manifest.read_text())
    with pytest.raises(ValueError, match="Duplicate case ID"):
        matrix.load_inventory(root, (registry,))


def test_new_nested_case_updates_summary_and_guide_index(inventory):
    root, manifest, case, registry, _, _ = inventory
    extra = dict(case)
    extra["case_id"] += "-variant"
    extra["test_node"] = case["test_node"].replace(case["case_id"], extra["case_id"])
    extra["documentation_anchor"] += "-variant"
    nested = manifest.parent / "new-category/cases.yaml"
    nested.parent.mkdir()
    nested.write_text(yaml.safe_dump({"cases": [extra]}))
    cases = matrix.load_inventory(root, (registry,))
    assert len(cases) == 2
    rendered = "\n".join(matrix.render_matrix(cases))
    assert "1 个精确高层注册键" in rendered
    assert "案例实现 2/2" in rendered
    index = "\n".join(matrix.render_case_index(cases, case["documentation_anchor"].split("#")[0]))
    assert f".. _{extra['documentation_anchor'].split('#')[1]}:" in index
    nested.unlink()
    assert len(matrix.load_inventory(root, (registry,))) == 1


def test_guide_anchor_requires_an_existing_label_or_generated_index(inventory):
    root, _, case, registry, guide, _ = inventory
    guide.write_text("# Guide\n")
    with pytest.raises(ValueError, match="Missing guide anchor"):
        matrix.load_inventory(root, (registry,))
    guide.write_text(f"({case['documentation_anchor'].split('#')[1]})=\n# Guide\n")
    loaded = matrix.load_inventory(root, (registry,))
    assert loaded[0]["existing_guide_anchor"]


def test_status_changes_recompute_counts_without_changing_registration(inventory):
    root, manifest, case, registry, _, _ = inventory
    before = "\n".join(matrix.render_matrix(matrix.load_inventory(root, (registry,))))
    assert "历史在线通过 1" in before
    case.update(online_status="implemented-unverified", enabled=False, reason="Pending bounded sample")
    manifest.write_text(yaml.safe_dump({"cases": [case]}))
    loaded = matrix.load_inventory(root, (registry,))
    after = "\n".join(matrix.render_matrix(loaded))
    assert "历史在线通过 0" in after
    assert "已实现、在线未验证 1" in after
    assert "1 个精确高层注册键" in after
    assert "案例实现 1/1" in after
    index = "\n".join(matrix.render_case_index(loaded, case["documentation_anchor"].split("#")[0]))
    assert f".. _{case['documentation_anchor'].split('#')[1]}:" in index
    assert f"<{matrix.case_label(case)}>" in index


def test_incremental_build_rediscovers_inventory(monkeypatch, inventory):
    root = inventory[0]
    # Use an uncached inventory so the event reflects new/deleted manifests.
    matrix_cases = [{"documentation_anchor": "guide/new-category#case"}]
    monkeypatch.setattr(matrix, "load_inventory", lambda project: matrix_cases)
    env = SimpleNamespace(srcdir=root / "docs/source", found_docs={
        "reference/support-matrix", "guide/new-category", "guide/unrelated",
    })
    assert matrix.refresh_case_documents(None, env, set(), set(), set()) == [
        "guide/new-category", "reference/support-matrix",
    ]
    assert matrix.refresh_case_documents(None, env, set(), set(), {"guide/new-category"}) == [
        "reference/support-matrix",
    ]
