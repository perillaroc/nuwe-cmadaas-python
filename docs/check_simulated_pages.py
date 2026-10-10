"""Check the executable tutorial inventory and public API coverage."""

import ast
import json
import re
from pathlib import Path


DOCS = Path(__file__).resolve().parent
SPECIAL_LINK = "{doc}`模拟数据与客户端注入 </guide/simulated-data>`"
CELL = re.compile(r"^```\{code-cell\} ipython3\n(.*?)^```", re.M | re.S)


def expected_api_calls(project_root: Path) -> set[str]:
    """Read public names from source without importing clients or configuration."""
    source = project_root / "src/nuwe_cmadaas"
    names = set()
    for family in ("obs", "model"):
        tree = ast.parse((source / family / "__init__.py").read_text(encoding="utf-8"))
        exported = next(
            node.value for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
        )
        names.update(ast.literal_eval(exported))
    tree = ast.parse((source / "music/client.py").read_text(encoding="utf-8"))
    client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CMADaaSClient")
    names.update(node.name for node in client.body if isinstance(node, ast.FunctionDef)
                 and node.name.startswith("callAPI_to_"))
    return names


def visible_api_calls(path: Path) -> set[str]:
    names = set()
    for cell in CELL.findall(path.read_text(encoding="utf-8")):
        if any(tag in cell for tag in (":tags: [hide-input]", ":tags: [remove-cell]", ":tags: [remove-input]")):
            continue
        code = re.sub(r"^:[a-z-]+:.*\n", "", cell, flags=re.M)
        tree = ast.parse(code, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if name.startswith(("retrieve_", "download_", "callAPI_to_")):
                names.add(name)
    return names


def check_page(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors = []
    if not re.search(r"\A---\n(?:(?!---\n).)*file_format: mystnb\n", content, re.S):
        errors.append("missing MyST-NB front matter")
    if not re.search(r"\A---\n(?:(?!---\n).)*kernelspec:\n", content, re.S):
        errors.append("missing kernel metadata")
    if not re.search(r"\A---\n(?:(?!---\n).)*simulated_data: true\n", content, re.S):
        errors.append("missing simulated_data metadata")
    first_cell = content.find("```{code-cell} ipython3")
    if first_cell < 0:
        errors.append("missing executable code cells")
    if SPECIAL_LINK not in content[:first_cell if first_cell >= 0 else None]:
        errors.append("missing visible simulated-data link before first example")
    cells = CELL.findall(content)
    if not cells or ":tags: [hide-input]" not in cells[0]:
        errors.append("first code cell must hide preparation input")
    if cells and any(tag in cells[0] for tag in ("remove-input", "remove-cell")):
        errors.append("preparation cell must remain expandable")
    if not any(":tags:" not in cell or ":tags: []" in cell for cell in cells[1:]):
        errors.append("missing visible API call and output cell")
    return errors


def check_inventory(docs_root: Path = DOCS, project_root: Path | None = None) -> list[str]:
    project_root = project_root or docs_root.parent
    inventory = json.loads((docs_root / "simulated-pages.json").read_text(encoding="utf-8"))
    entries = [inventory["template"], *inventory["pages"]]
    errors = []
    if len(entries) != len(set(entries)):
        errors.append("duplicate inventory entry")
    for entry in entries:
        path = (docs_root / entry).resolve()
        if not path.is_relative_to(docs_root) or not path.is_file():
            errors.append(f"{entry}: file missing or outside docs")
            continue
        errors.extend(f"{entry}: {issue}" for issue in check_page(path))

    marked = {
        path.relative_to(docs_root).as_posix()
        for path in (docs_root / "source").rglob("*.md")
        if re.search(r"^simulated_data: true$", path.read_text(encoding="utf-8"), re.M)
    }
    missing = marked - set(inventory["pages"])
    errors.extend(f"{entry}: marked page missing from inventory" for entry in sorted(missing))

    expected = expected_api_calls(project_root)
    visible = set()
    for entry in inventory["pages"]:
        path = (docs_root / entry).resolve()
        if path.is_relative_to(docs_root) and path.is_file():
            try:
                visible.update(visible_api_calls(path))
            except SyntaxError as exc:
                errors.append(f"{entry}: invalid visible Python cell: {exc}")
    errors.extend(f"{name}: no visible executable API call" for name in sorted(expected - visible))
    return errors


def main() -> int:
    errors = check_inventory()

    if errors:
        print("\n".join(errors))
        return 1
    inventory = json.loads((DOCS / "simulated-pages.json").read_text(encoding="utf-8"))
    print(f"Checked {len(inventory['pages'])} simulated pages and {len(expected_api_calls(DOCS.parent))} public API calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
