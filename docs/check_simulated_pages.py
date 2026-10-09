"""Check the executable tutorial inventory and its shared display contract."""

import json
import re
from pathlib import Path


DOCS = Path(__file__).resolve().parent
SOURCE = DOCS / "source"
SPECIAL_LINK = "{doc}`模拟数据与客户端注入 </guide/simulated-data>`"
CELL = re.compile(r"^```\{code-cell\} ipython3\n(.*?)^```", re.M | re.S)


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


def main() -> int:
    inventory = json.loads((DOCS / "simulated-pages.json").read_text(encoding="utf-8"))
    entries = [inventory["template"], *inventory["pages"]]
    errors = []
    if len(entries) != len(set(entries)):
        errors.append("duplicate inventory entry")
    for entry in entries:
        path = (DOCS / entry).resolve()
        if not path.is_relative_to(DOCS) or not path.is_file():
            errors.append(f"{entry}: file missing or outside docs")
            continue
        errors.extend(f"{entry}: {issue}" for issue in check_page(path))

    marked = {
        path.relative_to(DOCS).as_posix()
        for path in SOURCE.rglob("*.md")
        if re.search(r"^simulated_data: true$", path.read_text(encoding="utf-8"), re.M)
    }
    missing = marked - set(inventory["pages"])
    errors.extend(f"{entry}: marked page missing from inventory" for entry in sorted(missing))

    if errors:
        print("\n".join(errors))
        return 1
    print(f"Checked {len(entries)} simulated page template/page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
