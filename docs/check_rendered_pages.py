"""Validate visible tutorial links, expandable setup and outputs in Sphinx HTML."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


DOCS = Path(__file__).resolve().parent
SOURCE = DOCS / "source"


def check_page(page: Path, target: Path) -> list[str]:
    if not page.is_file():
        return ["rendered HTML is missing"]
    html = page.read_text(encoding="utf-8")
    if '<article class="bd-article">' not in html:
        return ["article body is missing"]
    article = html.split('<article class="bd-article">', 1)[1].split("</article>", 1)[0]
    first_cell = article.find('<div class="cell')
    errors = []
    if first_cell < 0:
        return ["rendered code cells are missing"]
    prelude = article[:first_cell]
    links = re.findall(r'<a\b[^>]*\bhref="([^"]+)"', prelude)
    if not any((page.parent / unquote(urlsplit(link).path)).resolve() == target.resolve()
               for link in links if not urlsplit(link).scheme and urlsplit(link).path):
        errors.append("visible simulated-data link is missing before the first code cell")
    setup = article[first_cell:first_cell + 200]
    if not re.match(r'<div class="cell tag_hide-input[^\"]*"[^>]*>\s*<details\b(?![^>]*\bopen\b)', setup):
        errors.append("first preparation cell is not collapsed and expandable")
    if not re.search(r'<div class="cell docutils container">\s*<div class="cell_input', article):
        errors.append("visible API code cell is missing")
    if '<div class="cell_output' not in article:
        errors.append("visible executed output is missing")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python docs/check_rendered_pages.py HTML_DIRECTORY")
        return 2
    html_root = Path(argv[1]).resolve()
    inventory = json.loads((DOCS / "simulated-pages.json").read_text(encoding="utf-8"))
    target = html_root / "guide/simulated-data.html"
    errors = []
    if not target.is_file():
        errors.append("guide/simulated-data.html: target is missing")
    for entry in inventory["pages"]:
        source = DOCS / entry
        page = html_root / source.relative_to(SOURCE).with_suffix(".html")
        errors.extend(f"{entry}: {issue}" for issue in check_page(page, target))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Checked rendered links, setup and output on {len(inventory['pages'])} simulated pages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
