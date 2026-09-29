"""Static integration-case manifest and simple runtime value references."""

from pathlib import Path

import pytest
import yaml


CASES_PATH = Path(__file__).with_name("cases.yaml")


def load_cases(family=None, *, implemented_only=False):
    """Read the public case mapping without loading credentials or a profile."""
    with CASES_PATH.open(encoding="utf-8") as stream:
        cases = yaml.safe_load(stream)["cases"]
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
        if set(value) == {"fixture"}:
            return request.getfixturevalue(value["fixture"])
        return {key: resolve_case_value(item, dataset, request) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_case_value(item, dataset, request) for item in value]
    return value
