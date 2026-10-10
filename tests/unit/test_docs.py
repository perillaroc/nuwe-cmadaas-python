from pathlib import Path

import pytest

from docs.check_simulated_pages import check_inventory, expected_api_calls, visible_api_calls


pytestmark = pytest.mark.unit


DOCS_ROOT = Path(__file__).parents[2] / "docs" / "source"


def test_simulated_inventory_covers_all_public_calls_in_visible_cells():
    assert check_inventory() == []
    assert len(expected_api_calls(DOCS_ROOT.parents[1])) == 17


def test_hidden_preparation_does_not_count_as_a_visible_tutorial_call(tmp_path):
    page = tmp_path / "hidden-only.md"
    page.write_text(
        "```{code-cell} ipython3\n:tags: [hide-input]\n"
        "retrieve_obs_station('synthetic')\n```\n"
        "```{code-cell} ipython3\nprint('result')\n```\n",
        encoding="utf-8",
    )
    assert visible_api_calls(page) == set()


def test_station_guide_uses_the_high_level_config_argument():
    content = (DOCS_ROOT / "guide" / "high-level" / "obs" / "station.md").read_text(
        encoding="utf-8"
    )

    assert "config_file=" not in content
    assert "config=" in content


def test_obs_grid_doc_describes_music_error_return():
    content = (DOCS_ROOT / "../.." / "src" / "nuwe_cmadaas" / "obs" / "grid.py")
    source = content.resolve().read_text(encoding="utf-8")

    assert "xr.DataArray or MusicError" in source
