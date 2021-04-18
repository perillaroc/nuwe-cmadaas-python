import typing


def _get_interface_id(interface_config: typing.Dict) ->str:
    interface_id = interface_config["name"]

    region_part = interface_config["region"]
    if region_part is not None:
        interface_id += "In" + region_part

    condition_part = "And".join(filter(None, [
        interface_config["time"],
        interface_config["station"]
    ]))
    if "level" in interface_config and interface_config["level"] is not None:
        condition_part = "And".join([condition_part, interface_config["level"]])

    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    fixed_interface_id = _fix_interface_id(interface_id)

    return fixed_interface_id


def _fix_interface_id(interface_id: str) -> str:
    mapper = {
        "getSurfEleByTimeRangeAndStaIdRange": "getSurfEleByTimeRangeAndStaIDRange"
    }
    return mapper.get(interface_id, interface_id)


def _get_region_params(region: typing.Dict, params: typing.Dict, interface_config: typing.Dict):
    region_type = region["type"]
    if region_type == "region":
        interface_config["region"] = "Region"
        v = region["admin_codes"]
        if isinstance(v, typing.List):
            v = ",".join(v)
        elif isinstance(v, int):
            v = str(v)
        params["adminCodes"] = v
    elif region_type == "rect":
        interface_config["region"] = "Rect"
        start_lat = region["start_latitude"]
        end_lat = region["end_latitude"]
        start_lon = region["start_longitude"]
        end_lon = region["end_longitude"]
        min_lat, max_lat = sorted([start_lat, end_lat])
        min_lon, max_lon = sorted([start_lon, end_lon])
        params.update({
            "minLat": f"{min_lat}",
            "minLon": f"{min_lon}",
            "maxLat": f"{max_lat}",
            "maxLon": f"{max_lon}",
        })
    elif region_type == "basin":
        interface_config["region"] = "Basin"
        v = region["basin_codes"]
        if isinstance(v, typing.List):
            v = ",".join(v)
        params["basinCodes"] = v
    else:
        raise ValueError(f"region type is not supported: {region_type}")