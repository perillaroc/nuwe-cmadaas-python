import math
import numbers
import typing
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd


@dataclass(frozen=True)
class NormalizedTime:
    """Internal representation of a high-level time selector."""

    kind: str
    value: object


@dataclass(frozen=True)
class NormalizedRegion:
    """Internal representation of a validated region selector."""

    kind: str
    value: object


@dataclass(frozen=True)
class NormalizedStation:
    """Internal representation of a station selector."""

    kind: str
    value: object


def normalize_timestamp(value, field_name: str = "time") -> pd.Timestamp:
    """Normalize a pandas or standard-library datetime to ``Timestamp``."""
    if isinstance(value, pd.Timestamp):
        timestamp = value
    elif isinstance(value, datetime):
        timestamp = pd.Timestamp(value)
    else:
        raise TypeError(
            f"{field_name} must be pandas.Timestamp or datetime.datetime; "
            f"got {type(value).__name__}"
        )
    if pd.isna(timestamp):
        raise ValueError(f"{field_name} must not be NaT")
    return timestamp


def normalize_time_interval(value, field_name: str = "time") -> pd.Interval:
    """Normalize and validate a timestamp interval."""
    if not isinstance(value, pd.Interval):
        raise TypeError(f"{field_name} must be a pandas.Interval")
    left = normalize_timestamp(value.left, f"{field_name}.left")
    right = normalize_timestamp(value.right, f"{field_name}.right")
    if left > right:
        raise ValueError(f"{field_name}.left must not exceed {field_name}.right")
    return pd.Interval(left, right, closed=value.closed)


def normalize_time_filter(value, field_name: str = "time") -> NormalizedTime | None:
    """Normalize all public high-level time selector forms without I/O."""
    if value is None:
        return None
    if isinstance(value, pd.Interval):
        return NormalizedTime("range", normalize_time_interval(value, field_name))
    if isinstance(value, (pd.Timestamp, datetime)):
        return NormalizedTime("single", normalize_timestamp(value, field_name))
    if isinstance(value, (pd.Timedelta, timedelta)):
        return NormalizedTime("latest", forecast_hours(value, field_name))
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError(f"{field_name} must not be an empty list")
        timestamps = tuple(
            normalize_timestamp(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        )
        return NormalizedTime("multiple", timestamps)
    raise TypeError(f"unsupported {field_name} type: {type(value).__name__}")


def time_filter_params(
    value,
    *,
    field_name: str = "time",
    single_key: str = "time",
    multiple_key: str = "times",
    range_key: str = "timeRange",
) -> tuple[NormalizedTime | None, dict]:
    """Return a normalized time selector and its MUSIC parameter mapping."""
    normalized = (
        value
        if isinstance(value, NormalizedTime)
        else normalize_time_filter(value, field_name)
    )
    if normalized is None:
        return None, {}
    if normalized.kind == "single":
        params = {single_key: get_time_string(normalized.value)}
    elif normalized.kind == "multiple":
        params = {
            multiple_key: ",".join(get_time_string(item) for item in normalized.value)
        }
    elif normalized.kind == "range":
        params = {range_key: get_time_range_string(normalized.value)}
    else:
        params = {"latestTime": str(normalized.value)}
    return normalized, params


def get_time_string(time) -> str:
    return normalize_timestamp(time).strftime("%Y%m%d%H%M%S")


def get_time_range_string(time_interval: pd.Interval) -> str:
    time_interval = normalize_time_interval(time_interval)
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
    elif isinstance(value, timedelta):
        value = pd.Timedelta(value)
    elif not isinstance(value, pd.Timedelta):
        raise TypeError(
            f"{field_name} must be a string, datetime.timedelta, or pandas.Timedelta; "
            f"got {type(value).__name__}"
        )

    hours = value / pd.Timedelta(hours=1)
    if not math.isfinite(float(hours)) or hours < 0 or not float(hours).is_integer():
        raise ValueError(
            f"{field_name} must be a non-negative whole-hour duration; got {value!r}"
        )
    return int(hours)


def normalize_station(value, field_name: str = "station") -> NormalizedStation | None:
    """Normalize a scalar/list station ID or a two-endpoint station range."""
    if value is None:
        return None
    if isinstance(value, (str, numbers.Integral)) and not isinstance(value, bool):
        if isinstance(value, str) and not value:
            raise ValueError(f"{field_name} must not be empty")
        return NormalizedStation("id", value)
    if isinstance(value, list):
        if not value:
            raise ValueError(f"{field_name} must not be an empty list")
        if not all(
            isinstance(item, (str, numbers.Integral)) and not isinstance(item, bool)
            for item in value
        ):
            raise TypeError(f"{field_name} list must contain strings or integers")
        if any(isinstance(item, str) and not item for item in value):
            raise ValueError(f"{field_name} list must not contain empty values")
        return NormalizedStation("ids", tuple(value))
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(f"{field_name} range must contain exactly two station IDs")
        if not all(
            isinstance(item, (str, numbers.Integral)) and not isinstance(item, bool)
            for item in value
        ):
            raise TypeError(f"{field_name} range must contain strings or integers")
        return NormalizedStation("range", value)
    raise TypeError(f"unsupported {field_name} type: {type(value).__name__}")


def station_filter_params(value) -> tuple[NormalizedStation | None, dict]:
    """Return normalized station selection and MUSIC parameter values."""
    normalized = normalize_station(value)
    if normalized is None:
        return None, {}
    if normalized.kind == "id":
        return normalized, {"staIds": normalized.value}
    if normalized.kind == "ids":
        return normalized, {"staIds": ",".join(str(item) for item in normalized.value)}
    return normalized, {
        "minStaId": normalized.value[0],
        "maxStaId": normalized.value[1],
    }


def normalize_level(value, field_name: str = "level"):
    """Validate a scalar, interval, or non-empty level collection."""
    if isinstance(value, pd.Interval):
        if not isinstance(value.left, numbers.Real) or not isinstance(value.right, numbers.Real):
            raise TypeError(f"{field_name} interval endpoints must be numbers")
        if value.left > value.right:
            raise ValueError(f"{field_name}.left must not exceed {field_name}.right")
        return value
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError(f"{field_name} must not be empty")
        if not all(
            isinstance(item, (numbers.Real, str)) and not isinstance(item, bool)
            for item in value
        ):
            raise TypeError(f"{field_name} must contain numbers or strings")
        if any(isinstance(item, str) and not item for item in value):
            raise ValueError(f"{field_name} must not contain empty values")
        return tuple(value)
    if not isinstance(value, (numbers.Real, str)) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a number, string, interval, or collection")
    if isinstance(value, str) and not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def validate_level_pair(level_type, level, field_name: str = "level") -> None:
    """Validate that a level and its level type are supplied together."""
    if (level_type is None) != (level is None):
        raise ValueError(f"{field_name}_type and {field_name} must be provided together")


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


def normalize_region(region) -> NormalizedRegion:
    """Normalize a region mapping to a validated internal representation."""
    if not isinstance(region, Mapping):
        raise TypeError(f"region must be a mapping; got {type(region).__name__}")
    if "type" not in region:
        raise ValueError("region.type is required")

    region_type = region["type"]
    if region_type == "region":
        if "admin_codes" not in region:
            raise ValueError("region.admin_codes is required")
        return NormalizedRegion(
            "region", _validate_code_values(region["admin_codes"], "region.admin_codes")
        )
    if region_type == "basin":
        if "basin_codes" not in region:
            raise ValueError("region.basin_codes is required")
        return NormalizedRegion(
            "basin", _validate_code_values(region["basin_codes"], "region.basin_codes")
        )
    if region_type != "rect":
        raise ValueError(f"region type is not supported: {region_type}")

    required = ("start_longitude", "end_longitude", "start_latitude", "end_latitude")
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
    return NormalizedRegion("rect", (min_lat, min_lon, max_lat, max_lon))


def get_region_params(region: typing.Dict, params: typing.Dict, interface_config: typing.Dict):
    normalized = (
        region if isinstance(region, NormalizedRegion) else normalize_region(region)
    )
    if normalized.kind == "region":
        interface_config["region"] = "Region"
        params["adminCodes"] = normalized.value
    elif normalized.kind == "rect":
        interface_config["region"] = "Rect"
        min_lat, min_lon, max_lat, max_lon = normalized.value
        params.update({
            "minLat": f"{min_lat}",
            "minLon": f"{min_lon}",
            "maxLat": f"{max_lat}",
            "maxLon": f"{max_lon}",
        })
    elif normalized.kind == "basin":
        interface_config["region"] = "Basin"
        params["basinCodes"] = normalized.value

    return params, interface_config
