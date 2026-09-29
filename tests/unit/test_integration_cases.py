"""Guard the static case inventory against registry drift."""

from nuwe_cmadaas.interfaces import INTERFACE_SPECS
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
    assert len(cases) == len(expected)
    assert actual == expected

    for case in cases:
        assert case["documentation_anchor"]
        assert case["profile_key"]
        if case["implemented"]:
            assert case["public_kwargs"]
            assert case["expected_return_contract"]
            assert case["test_node"]
            assert case["online_status"] in {
                "implemented-unverified", "passed", "skipped", "failed", "blocked-contract"
            }
