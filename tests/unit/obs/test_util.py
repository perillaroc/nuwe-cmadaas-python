import pytest

from nuwe_cmadaas.obs.util import _get_interface_id


pytestmark = pytest.mark.unit


def test_get_interface_id_builds_typical_observation_name():
    assert _get_interface_id(
        {
            "name": "getSurfEle",
            "region": "Rect",
            "time": "Time",
            "station": "StaID",
            "level": None,
        }
    ) == "getSurfEleInRectByTimeAndStaID"


def test_get_interface_id_handles_empty_observation_conditions():
    assert _get_interface_id(
        {
            "name": "getSurfEle",
            "region": None,
            "time": None,
            "station": None,
            "level": None,
        }
    ) == "getSurfEle"
