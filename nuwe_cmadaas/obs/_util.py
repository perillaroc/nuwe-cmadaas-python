from typing import TypedDict, Optional

from nuwe_cmadaas._log import logger


class InterfaceConfig(TypedDict):
    name: str
    region: Optional[str]
    time: Optional[str]
    station: Optional[str]
    level: Optional[str]


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    interface_id = interface_config["name"]

    region_part = interface_config["region"]
    if region_part is not None:
        interface_id += "In" + region_part

    condition_part = ""

    if "time" in interface_config and interface_config["time"] is not None:
        condition_part = "And".join(filter(None, [condition_part, interface_config["time"]]))

    if "station" in interface_config and interface_config["station"] is not None:
        condition_part = "And".join(filter(None, [condition_part, interface_config["station"]]))

    if "level" in interface_config and interface_config["level"] is not None:
        condition_part = "And".join(filter(None, [condition_part, interface_config["level"]]))

    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    fixed_interface_id = _fix_interface_id(interface_id)

    return fixed_interface_id


def _fix_interface_id(interface_id: str) -> str:
    mapper = {
        "getSurfEleByTimeRangeAndStaIdRange": "getSurfEleByTimeRangeAndStaIDRange"
    }
    return mapper.get(interface_id, interface_id)


def _fix_params(interface_id, params):
    if interface_id in (
        "getUparGpsEleByTimeAndStaID",
        "getUparGpsEleInRectByTime",
        "not_getUparGpsEleInRegionByTime"
    ):
        logger.warning("UparGps don't use dataCode!")
        del params["dataCode"]
    return params
