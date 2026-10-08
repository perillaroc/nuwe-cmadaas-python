from typing import TypedDict, Optional

from nuwe_cmadaas.interfaces import resolve_interface


class InterfaceConfig(TypedDict):
    name: str
    region: Optional[str]
    time: Optional[str]
    station: Optional[str]
    level: Optional[str]


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    name = interface_config["name"]
    family = {
        "getSurfEle": "obs_station",
        "getSurfFile": "obs_file",
        "getUparEle": "obs_upper",
        "getUparGpsEle": "obs_upper_gps",
        "getUparLightEle": "obs_upper_light",
        "getUparArdEle": "obs_upper_ard",
        "getSurfLatestTime": "obs_station_latest",
        "getNafpLatestTime": "model_file_latest",
    }.get(name)
    if family is None:
        raise ValueError(f"unregistered high-level interface base: {name}")
    return resolve_interface(family, _features_from_config(interface_config)).interface_id


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    region = interface_config.get("region")
    if region is not None:
        features.add({"Rect": "region_rect", "Region": "region_region", "Basin": "region_basin"}.get(region, region))
    time = interface_config.get("time")
    if time == "TimeRange":
        features.add("time_range")
    elif time is not None:
        features.add("time")
    station = interface_config.get("station")
    if station == "StaIdRange":
        features.add("station_range")
    elif station == "StaLevels":
        features.add("station_level")
    elif station is not None:
        features.add("station")
    level = interface_config.get("level")
    if level is not None:
        features.add({
            "Press": "level_press",
            "Height": "level_height",
            "Vertical": "level_vertical",
        }.get(level, "level"))
    return frozenset(features)


def _fix_params(interface_id, params):
    """Two GPS interfaces reject dataCode despite listing it as type D."""
    if interface_id in {
        "getUparGpsEleByTimeAndStaID",
        "getUparGpsEleInRectByTime",
    }:
        params.pop("dataCode", None)
    return params
