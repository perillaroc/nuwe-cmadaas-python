import math
import numbers
import typing
from collections.abc import Mapping

import pandas as pd


def get_time_string(time: pd.Timestamp) -> str:
    return time.strftime("%Y%m%d%H%M%S")


def get_time_range_string(time_interval: pd.Interval) -> str:
    left = "[" if time_interval.closed_left else ")"
    start = get_time_string(time_interval.left)
    right = "]" if time_interval.closed_right else ")"
    end = get_time_string(time_interval.right)
    return f"{left}{start},{end}{right}"


def forecast_hours(value, field_name: str = "forecast_time") -> int:
    """Convert a supported forecast lead value to an integral hour count."""
    if isinstance(value, str):
        try:
            value = pd.to_timedelta(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be a duration convertible to whole hours; "
                f"got {value!r}"
            ) from exc
    elif not isinstance(value, pd.Timedelta):
        raise TypeError(
            f"{field_name} must be a string or pandas.Timedelta; "
            f"got {type(value).__name__}"
        )

    hours = value / pd.Timedelta(hours=1)
    if not math.isfinite(float(hours)) or hours < 0 or not float(hours).is_integer():
        raise ValueError(
            f"{field_name} must be a non-negative whole-hour duration; got {value!r}"
        )
    return int(hours)


def forecast_hour_range(value, field_name: str = "forecast_time") -> tuple[int, int]:
    """Validate and convert a two-endpoint forecast lead range."""
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} range must be a two-item tuple")
    if len(value) != 2:
        raise ValueError(f"{field_name} range must contain exactly two endpoints")

    start, end = (
        forecast_hours(endpoint, f"{field_name}[{index}]")
        for index, endpoint in enumerate(value)
    )
    if start > end:
        raise ValueError(f"{field_name} range start must not exceed its end")
    return start, end


def validate_count(count, field_name: str = "count") -> None:
    """Validate a MUSIC record limit before a request is sent."""
    if count is None:
        return
    if isinstance(count, bool) or not isinstance(count, numbers.Integral):
        raise TypeError(f"{field_name} must be a positive integer; got {count!r}")
    if count <= 0:
        raise ValueError(f"{field_name} must be a positive integer; got {count!r}")


def _finite_coordinate(value, field_name: str, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise TypeError(f"{field_name} must be a finite number; got {value!r}")
    value = float(value)
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(
            f"{field_name} must be finite and between {lower} and {upper}; got {value!r}"
        )
    return value


def validate_lat_lon_pair(value, field_name: str = "point") -> tuple[float, float]:
    """Validate one point represented as ``(latitude, longitude)``."""
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{field_name} must contain exactly latitude and longitude")
    return (
        _finite_coordinate(value[0], f"{field_name}[0]", -90, 90),
        _finite_coordinate(value[1], f"{field_name}[1]", -180, 180),
    )


def _validate_code_values(value, field_name: str):
    if isinstance(value, (str, numbers.Integral)) and not isinstance(value, bool):
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{field_name} must not be empty")
        return str(value) if isinstance(value, numbers.Integral) else value
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError(f"{field_name} must not be empty")
        if not all(isinstance(item, (str, numbers.Integral)) and not isinstance(item, bool)
                   for item in value):
            raise TypeError(f"{field_name} must contain only strings or integers")
        if any(isinstance(item, str) and not item.strip() for item in value):
            raise ValueError(f"{field_name} must not contain empty values")
        return ",".join(str(item) for item in value)
    raise TypeError(f"{field_name} must be a string, integer, or non-empty list")


def get_region_params(region: typing.Dict, params: typing.Dict, interface_config: typing.Dict):
    if not isinstance(region, Mapping):
        raise TypeError(f"region must be a mapping; got {type(region).__name__}")
    if "type" not in region:
        raise ValueError("region.type is required")
    region_type = region["type"]
    if region_type == "region":
        interface_config["region"] = "Region"
        if "admin_codes" not in region:
            raise ValueError("region.admin_codes is required")
        v = _validate_code_values(region["admin_codes"], "region.admin_codes")
        params["adminCodes"] = v
    elif region_type == "rect":
        interface_config["region"] = "Rect"
        required = (
            "start_longitude", "end_longitude", "start_latitude", "end_latitude"
        )
        missing = [key for key in required if key not in region]
        if missing:
            raise ValueError(f"region is missing field(s): {', '.join(missing)}")
        start_lat = _finite_coordinate(
            region["start_latitude"], "region.start_latitude", -90, 90
        )
        end_lat = _finite_coordinate(
            region["end_latitude"], "region.end_latitude", -90, 90
        )
        start_lon = _finite_coordinate(
            region["start_longitude"], "region.start_longitude", -180, 180
        )
        end_lon = _finite_coordinate(
            region["end_longitude"], "region.end_longitude", -180, 180
        )
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
        if "basin_codes" not in region:
            raise ValueError("region.basin_codes is required")
        v = _validate_code_values(region["basin_codes"], "region.basin_codes")
        params["basinCodes"] = v
    else:
        raise ValueError(f"region type is not supported: {region_type}")

    return params, interface_config
