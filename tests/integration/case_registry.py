"""Load category manifests and resolve simple runtime value references."""

from pathlib import Path

import pytest
import yaml


CASES_ROOT = Path(__file__).parent


def load_cases(family=None, *, implemented_only=False):
    """Aggregate manifests in path order and reject globally duplicate IDs.

    Discovery and validation run before filtering, without reading credentials
    or a service profile. Adding a category needs no loader registration.
    """
    paths = sorted(CASES_ROOT.rglob("cases.yaml"))
    if not paths:
        raise ValueError(f"No integration case manifests found under {CASES_ROOT}")
    cases = []
    sources = {}
    for path in paths:
        with path.open(encoding="utf-8") as stream:
            manifest = yaml.safe_load(stream)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("cases"), list):
            raise ValueError(f"Invalid case manifest at {path}: expected a cases list")
        for case in manifest["cases"]:
            if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
                raise ValueError(f"Invalid case record at {path}: expected a string case_id")
            case_id = case["case_id"]
            if case_id in sources:
                raise ValueError(
                    f"Duplicate case_id {case_id!r} in {sources[case_id]} and {path}"
                )
            sources[case_id] = path
            cases.append(case)
    if family is not None:
        cases = [case for case in cases if case["family"] == family]
    if implemented_only:
        cases = [case for case in cases if case["implemented"]]
    return cases


def case_parameters(family):
    """Give each implemented case a stable pytest ID and its declared tier."""
    parameters = []
    for case in load_cases(family, implemented_only=True):
        tier = case["tier"]
        if tier not in {"smoke", "extended"}:
            raise ValueError(f"Invalid tier for {case['case_id']}: {tier}")
        parameters.append(
            pytest.param(case, id=case["case_id"], marks=getattr(pytest.mark, tier))
        )
    return parameters


def resolve_case_value(value, dataset, request):
    """Resolve literal, dataset-profile or pytest-fixture values at test runtime."""
    if isinstance(value, dict):
        if set(value) == {"profile"}:
            return dataset[value["profile"]]
        if set(value) == {"tuple"}:
            return tuple(resolve_case_value(value["tuple"], dataset, request))
        if set(value) == {"fixture"}:
            return request.getfixturevalue(value["fixture"])
        return {key: resolve_case_value(item, dataset, request) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_case_value(item, dataset, request) for item in value]
    return value
