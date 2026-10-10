"""Build case references from public manifests, without pytest or service profiles."""

import ast
from collections import Counter, defaultdict
from pathlib import Path
import re

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.errors import ExtensionError
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles
import yaml

import nuwe_cmadaas
from nuwe_cmadaas.interfaces import INTERFACE_SPECS
from nuwe_cmadaas.music import CMADaaSClient


STATUS = {
    "passed": "历史在线通过",
    "failed": "历史在线失败",
    "implemented-unverified": "已实现、在线未验证",
}
RETURN_TYPES = {
    "dataframe": "pandas.DataFrame", "dataarray": "xarray.DataArray",
    "paths": "list[Path]", "str": "str", "Array2D": "Array2D",
    "GridArray2D": "GridArray2D", "GridScalar2D": "GridScalar2D",
    "GridVector2D": "GridVector2D", "FilesInfo": "FilesInfo", "DataBlock": "DataBlock",
}


def manifest_paths(root):
    return sorted((root / "tests/integration").rglob("cases.yaml"))


def case_label(case):
    return "support-case-" + case["case_id"].lower()


def load_inventory(root, specs=INTERFACE_SPECS):
    """Validate registry coverage and both ends of every documentation trace."""
    cases, sources = [], {}
    paths = manifest_paths(root)
    if not paths:
        raise ValueError("No integration case manifests found")
    required = {
        "case_id", "family", "query_features", "interface_id", "public_function",
        "public_kwargs", "expected_return_contract", "profile_key", "tier", "enabled",
        "implemented", "online_status", "reason", "test_node", "documentation_anchor",
    }
    for path in paths:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("cases"), list):
            raise ValueError(f"Invalid case manifest: {path}")
        for original in manifest["cases"]:
            if not isinstance(original, dict) or required - original.keys():
                raise ValueError(f"Incomplete case record: {path}")
            case = dict(original)
            case_id = case["case_id"]
            if not isinstance(case_id, str) or not re.fullmatch(r"[A-Za-z0-9-]+", case_id):
                raise ValueError(f"Invalid case ID: {case_id!r}")
            if case_id.lower() in sources:
                raise ValueError(f"Duplicate case ID: {case_id}")
            sources[case_id.lower()] = path
            case["manifest_path"] = path.relative_to(root).as_posix()
            cases.append(case)

    spec_index = {(s.family, tuple(sorted(s.query_features))): s for s in specs}
    if len(spec_index) != len(specs):
        raise ValueError("Duplicate production registry key")
    mapped = set()
    for case in cases:
        case_id = case["case_id"]
        features = case["query_features"]
        if features != sorted(set(features)):
            raise ValueError(f"Unnormalized query features: {case_id}")
        key = case["family"], tuple(features)
        if case["family"].startswith("music_"):
            case["registration"] = "底层方法；interface 不受高层注册表限制"
        else:
            spec = spec_index.get(key)
            if spec is None or spec.interface_id != case["interface_id"]:
                raise ValueError(f"Unregistered or mismatched interface: {case_id}")
            mapped.add(key)
            case["registration"] = "精确高层注册键；响应 " + spec.return_type
        function = case["public_function"]
        if function.startswith("CMADaaSClient."):
            public = getattr(CMADaaSClient, function.split(".", 1)[1], None)
        else:
            public = getattr(nuwe_cmadaas, function, None)
        if not callable(public):
            raise ValueError(f"Unknown public entry: {case_id}")
        if case["expected_return_contract"].get("kind") not in RETURN_TYPES:
            raise ValueError(f"Unknown return contract: {case_id}")
        if case["online_status"] not in STATUS or not case["reason"]:
            raise ValueError(f"Invalid verification status: {case_id}")
        if case["online_status"] == "passed" and not case.get("last_verified_environment_and_time"):
            raise ValueError(f"Missing historical verification context: {case_id}")
        for flag in ("implemented", "enabled"):
            if type(case[flag]) is not bool:
                raise ValueError(f"Invalid {flag} flag: {case_id}")
        if not case["implemented"] and case["online_status"] != "implemented-unverified":
            raise ValueError(f"Unimplemented case has an online result: {case_id}")
        test_path, node = case["test_node"].split("::", 1)
        if not test_path.startswith("tests/integration/") or ".." in Path(test_path).parts:
            raise ValueError(f"Invalid test path: {case_id}")
        test_file = root / test_path
        function_name, _, pytest_id = node.partition("[")
        if not test_file.is_file() or pytest_id != case_id + "]":
            raise ValueError(f"Invalid test node: {case_id}")
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
        if function_name not in {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}:
            raise ValueError(f"Missing test function: {case_id}")
        docname, anchor = case["documentation_anchor"].split("#", 1)
        if not docname.startswith("guide/") or ".." in Path(docname).parts:
            raise ValueError(f"Invalid guide path: {case_id}")
        guide = root / "docs/source" / (docname + ".md")
        if not guide.is_file():
            raise ValueError(f"Missing guide: {case_id}")
        content = guide.read_text(encoding="utf-8")
        existing_anchor = re.search(rf"^\({re.escape(anchor)}\)=$", content, re.MULTILINE)
        if not existing_anchor and "```{cmadaas-case-index}" not in content:
            raise ValueError(f"Missing guide anchor or generated index: {case_id}")
        case["existing_guide_anchor"] = bool(existing_anchor)
    if mapped != set(spec_index):
        raise ValueError(f"Missing registered combinations: {sorted(set(spec_index) - mapped)}")
    return cases


def _table(headers, rows):
    lines = [".. list-table::", "   :header-rows: 1", "", "   * - " + headers[0]]
    lines.extend("     - " + cell for cell in headers[1:])
    for row in rows:
        for index, cell in enumerate(row):
            parts = cell.splitlines()
            lines.append(("   * - " if index == 0 else "     - ") + parts[0])
            lines.extend("       " + part if part else "" for part in parts[1:])
    return lines + [""]


def render_matrix(cases):
    """Produce a summary and complete, individually addressable case records."""
    groups = defaultdict(list)
    for case in cases:
        groups[case["family"]].append(case)
    high = [c for c in cases if not c["family"].startswith("music_")]
    keys = {(c["family"], tuple(c["query_features"])) for c in high}
    methods = {c["public_function"] for c in cases if c["family"].startswith("music_")}
    entries = {c["public_function"] for c in high if not c["public_function"].startswith("CMADaaSClient.")}
    counts = Counter(c["online_status"] for c in cases)
    lines = [
        f"清单共 {len(cases)} 条案例：{len(keys)} 个精确高层注册键，"
        f"{len(high)} 条注册组合案例覆盖 {len(entries)} 个高层入口；"
        f"{len(cases) - len(high)} 条底层案例覆盖 {len(methods)} 个方法。",
        "",
        f"案例实现 {sum(c['implemented'] for c in cases)}/{len(cases)}；"
        f"清单启用 {sum(c['enabled'] for c in cases)}/{len(cases)}（实际运行还需私有 profile 开关）。",
        "",
        "历史在线状态：" + "；".join(f"{STATUS[s]} {counts[s]}" for s in STATUS) + "。",
        "",
    ]
    rows = []
    for family, group in groups.items():
        states = Counter(c["online_status"] for c in group)
        registered = len({tuple(c["query_features"]) for c in group}) if not family.startswith("music_") else "底层"
        rows.append([
            f":ref:`{family} <support-family-{family}>`", str(registered), str(len(group)),
            str(sum(c["implemented"] for c in group)),
            " / ".join(str(states[s]) for s in STATUS),
        ])
    lines += _table(["family", "注册键", "案例", "已实现", "历史通过 / 失败 / 未验证"], rows)
    for family, group in groups.items():
        lines += [f".. _support-family-{family}:", "", family, "-" * len(family), ""]
        rows = []
        for case in group:
            rows.append([
                f":ref:`{case['case_id']} <{case_label(case)}>`",
                "``" + (" + ".join(case["query_features"]) or "<none>") + "``",
                f"``{case['interface_id']}``", STATUS[case["online_status"]],
            ])
        lines += _table(["案例详情", "查询组合", "MUSIC interface", "历史在线状态"], rows)
        for case in group:
            case_id = case["case_id"]
            anchor = case["documentation_anchor"].split("#", 1)[1]
            lines += [f".. _{case_label(case)}:", "", case_id, "~" * len(case_id), ""]
            lines += [
                f"MUSIC interface：``{case['interface_id']}``；查询组合：``"
                + (" + ".join(case["query_features"]) or "<none>") + "``。", "",
                f"公开入口：``{case['public_function']}``；返回类型："
                f"``{RETURN_TYPES[case['expected_return_contract']['kind']]}``。", "",
                f"登记：{case['registration']}；案例实现：{'已实现' if case['implemented'] else '未实现'}；"
                f"清单开关：{'启用' if case['enabled'] else '关闭'}；tier：``{case['tier']}``。", "",
                f"指南：:ref:`{case['documentation_anchor']} <{anchor}>`。", "",
                f"测试节点：``{case['test_node']}``。", "",
                f"源码：:download:`测试文件 <../../../{case['test_node'].split('::', 1)[0]}>`；"
                f":download:`案例清单 <../../../{case['manifest_path']}>`；profile key：``{case['profile_key']}``。", "",
                f"真实服务验证：{STATUS[case['online_status']]}（``{case['online_status']}``）。", "",
                "原因 / 实际结果：" + " ".join(case["reason"].split()), "",
                "历史环境、时间与资料：" + " ".join(str(case.get("last_verified_environment_and_time") or "未记录；不计在线通过").split()), "",
            ]
            for field, title in [("run_prerequisite", "重跑前提"), ("verification_blocker", "验证阻塞"),
                                 ("recommended_data_code", "建议资料"), ("alternative_data_code_probe", "替代资料探测")]:
                if case.get(field):
                    lines += [title + "：" + " ".join(str(case[field]).split()), ""]
            lines += ["清单中的调用参数与独立返回断言（profile / fixture 引用在测试运行时解析）：", "", ".. code-block:: yaml", ""]
            contract = {"public_kwargs": case["public_kwargs"], "expected_return_contract": case["expected_return_contract"]}
            lines += ["   " + line for line in yaml.safe_dump(contract, allow_unicode=True, sort_keys=False).splitlines()]
            lines.append("")
    return lines


def render_case_index(cases, docname):
    """Fill missing guide anchors and link each guide case back to its evidence."""
    selected = [c for c in cases if c["documentation_anchor"].split("#", 1)[0] == docname]
    if not selected:
        raise ValueError(f"No cases refer to guide: {docname}")
    lines = ["本页关联的全部清单案例如下。已有示例锚点保留；其余案例锚点由清单生成，", "详情链接包含测试节点、参数、返回断言与历史在线状态；模拟执行不更新这些状态。", ""]
    rows = []
    for case in selected:
        prefix = ""
        if not case["existing_guide_anchor"]:
            anchor = case["documentation_anchor"].split("#", 1)[1]
            prefix = f".. _{anchor}:\n\n"
        rows.append([
            prefix + f":ref:`{case['case_id']} <{case_label(case)}>`",
            f"``{case['interface_id']}``", STATUS[case["online_status"]],
        ])
    lines += _table(["案例详情", "MUSIC interface", "历史在线状态"], rows)
    return lines


class CaseDirective(SphinxDirective):
    def run(self):
        root = Path(self.env.srcdir).parents[1]
        try:
            cases = load_inventory(root)
            for path in manifest_paths(root):
                self.env.note_dependency(str(path))
            for case in cases:
                self.env.note_dependency(str(root / case["test_node"].split("::", 1)[0]))
                docname = case["documentation_anchor"].split("#", 1)[0]
                self.env.note_dependency(str(root / "docs/source" / (docname + ".md")))
            lines = (render_matrix(cases) if self.name == "cmadaas-support-matrix"
                     else render_case_index(cases, self.env.docname))
            if self.name == "cmadaas-case-index":
                # Guide pages use MyST; parse generated RST with its RST bridge.
                lines = ["```{eval-rst}", *lines, "```"]
        except (ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
            raise ExtensionError(f"Invalid support matrix inventory: {exc}") from exc
        container = nodes.container()
        nested_parse_with_titles(self.state, StringList(lines, source=self.get_source_info()[0]), container)
        if self.name == "cmadaas-case-index":
            # eval-rst parses a separate document. Register its new row targets
            # in the owning MyST document so Sphinx can resolve :ref: links.
            missing = {
                case["documentation_anchor"].split("#", 1)[1] for case in cases
                if case["documentation_anchor"].split("#", 1)[0] == self.env.docname
                and not case["existing_guide_anchor"]
            }
            for node in container.findall(nodes.Element):
                if missing.intersection(node.get("names", [])):
                    self.state.document.note_explicit_target(node)
        return list(container.children)


def refresh_case_documents(app, env, added, changed, removed):
    """Rediscover new/deleted manifests and registry keys even on incremental builds."""
    root = Path(env.srcdir).parents[1]
    documents = {"reference/support-matrix"}
    for case in load_inventory(root):
        documents.add(case["documentation_anchor"].split("#", 1)[0])
    return sorted(documents & env.found_docs - removed)


def setup(app):
    app.add_directive("cmadaas-support-matrix", CaseDirective)
    app.add_directive("cmadaas-case-index", CaseDirective)
    app.connect("env-get-outdated", refresh_case_documents)
    return {"version": "1", "parallel_read_safe": True, "parallel_write_safe": True}
