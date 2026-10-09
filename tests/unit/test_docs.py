from pathlib import Path

import pytest


pytestmark = pytest.mark.unit


DOCS_ROOT = Path(__file__).parents[2] / "docs" / "source"


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
