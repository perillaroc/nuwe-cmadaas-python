import pandas as pd
import pytest


@pytest.fixture
def music_cycle_time(base_time):
    """A recent 06 UTC model cycle, formatted for native MUSIC parameters."""
    return (base_time + pd.Timedelta(hours=6)).strftime("%Y%m%d%H%M%S")


@pytest.fixture
def music_save_json_path(tmp_path):
    return str(tmp_path / "result.json")


@pytest.fixture
def music_save_xml_path(tmp_path):
    return str(tmp_path / "result.xml")


@pytest.fixture
def music_save_text_path(tmp_path):
    return str(tmp_path / "result.text")


@pytest.fixture
def music_save_html_path(tmp_path):
    return str(tmp_path / "result.html")
