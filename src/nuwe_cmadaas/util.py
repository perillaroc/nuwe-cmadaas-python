import typing

import pandas as pd


def get_time_string(time: pd.Timestamp) -> str:
    return time.strftime("%Y%m%d%H%M%S")


def get_time_range_string(time_interval: pd.Interval) -> str:
    left = "[" if time_interval.closed_left else ")"
    start = get_time_string(time_interval.left)
    right = "[" if time_interval.closed_right else ")"
    end = get_time_string(time_interval.right)
    return f"{left}{start},{end}{right}"


def get_region_params(region: typing.Dict, params: typing.Dict, interface_config: typing.Dict):
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

    return params, interface_config
