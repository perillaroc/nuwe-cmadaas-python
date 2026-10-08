"""Fixed MUSIC interface specifications used by the high-level API.

The MUSIC-compatible client accepts arbitrary interface ids.  The high-level
API intentionally does not: only combinations with a stable return contract
are registered here.
"""

from dataclasses import dataclass
from typing import Iterable, Mapping

from nuwe_cmadaas.music.errors import CMADaaSQueryError


class UnsupportedQueryError(CMADaaSQueryError):
    """Raised when a high-level query has no registered MUSIC interface."""


@dataclass(frozen=True)
class InterfaceSpec:
    """Description of one high-level MUSIC interface."""

    family: str
    interface_id: str
    return_type: str
    query_features: frozenset[str]
    required_params: frozenset[str] = frozenset()
    optional_params: frozenset[str] = frozenset()


def _features(*names: str) -> frozenset[str]:
    return frozenset(names)


def _make_specs(
    family: str,
    return_type: str,
    declarations: Mapping[frozenset[str], tuple[str, frozenset[str]]],
) -> list[InterfaceSpec]:
    return [
        InterfaceSpec(
            family=family,
            interface_id=interface_id,
            return_type=return_type,
            query_features=feature_set,
            required_params=required_params,
        )
        for feature_set, (interface_id, required_params) in declarations.items()
    ]


_MODEL_GRID_SUFFIXES = {
    _features(): "",
    _features("time"): "ByTime",
    _features("level"): "ByLevel",
    _features("valid_time"): "ByValidtime",
    _features("time", "level"): "ByTimeAndLevel",
    _features("time", "valid_time"): "ByTimeAndValidtime",
    _features("level", "valid_time"): "ByLevelAndValidtime",
    _features("time", "level", "valid_time"): "ByTimeAndLevelAndValidtime",
    _features("region"): "InRect",
    _features("region", "time"): "InRectByTime",
    _features("region", "level"): "InRectByLevel",
    _features("region", "valid_time"): "InRectByValidtime",
    _features("region", "time", "level"): "InRectByTimeAndLevel",
    _features("region", "time", "valid_time"): "InRectByTimeAndValidtime",
    _features("region", "level", "valid_time"): "InRectByLevelAndValidtime",
    _features("region", "time", "level", "valid_time"):
        "InRectByTimeAndLevelAndValidtime",
    _features("time", "level", "valid_time", "number"):
        "ByTimeAndLevelAndValidtimeAndFcstMember",
    _features("region", "time", "level", "valid_time", "number"):
        "InRectByTimeAndLevelAndValidtimeAndFcstMember",
}

_CATALOG_MODEL_GRID_IDS = {
    "model_grid_forecast": {
        "getNafpEleGridByTime",
        "getNafpEleGridByTimeAndLevelAndValidtime",
        "getNafpEleGridInRectByTime",
        "getNafpEleGridInRectByTimeAndLevelAndValidtime",
        "getNafpEleGridByTimeAndLevelAndValidtimeAndFcstMember",
        "getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember",
    },
    "model_grid_analysis": {
        "getNafpAnaEleGridByTimeAndLevel",
        "getNafpAnaEleGridInRectByTimeAndLevel",
    },
}


def _model_grid_declarations(base: str) -> dict[frozenset[str], tuple[str, frozenset[str]]]:
    required = {"dataCode", "fcstEle"}
    result = {}
    for feature_set, suffix in _MODEL_GRID_SUFFIXES.items():
        feature_params = set()
        if "time" in feature_set:
            feature_params.add("time")
        if "level" in feature_set:
            feature_params.update(("levelType", "fcstLevel"))
        if "valid_time" in feature_set:
            feature_params.add("validTime")
        if "number" in feature_set:
            feature_params.add("fcstMember")
        if "region" in feature_set:
            feature_params.update(("minLat", "minLon", "maxLat", "maxLon"))
        result[feature_set] = (base + suffix, frozenset(required | feature_params))
    return result


_MODEL_FILE_DECLARATIONS = {
    _features("time"): ("getNafpFileByTime", _features("dataCode", "time")),
    _features("time_range"): ("getNafpFileByTimeRange", _features("dataCode", "timeRange")),
    # The catalog requires levelType for element searches, even without fcstLevel.
    # elements is optional on these file interfaces.
    _features("element", "time"): ("getNafpFileByElementAndTime", _features("dataCode", "fcstEle", "time", "levelType")),
    _features("element", "time_range"): ("getNafpFileByElementAndTimeRange", _features("dataCode", "fcstEle", "timeRange", "levelType")),
    _features("element", "time", "level"): ("getNafpFileByElementAndTimeAndLevel", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel")),
    _features("element", "time", "valid_time"): ("getNafpFileByElementAndTimeAndValidtime", _features("dataCode", "fcstEle", "time", "levelType", "validTime")),
    _features("element", "time", "level", "valid_time"): ("getNafpFileByElementAndTimeAndLevelAndValidtime", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel", "validTime")),
}


_OBS_STATION_SUFFIXES = {
    # Exact station interfaces from the CMADaaS SURF_API catalog.
    _features("time"): "ByTime",
    _features("time_range"): "ByTimeRange",
    _features("station"): "ByStaID",
    _features("time", "station"): "ByTimeAndStaID",
    _features("time", "station_range"): "ByTimeAndStaIdRange",
    _features("time_range", "station"): "ByTimeRangeAndStaID",
    _features("time_range", "station_range"): "ByTimeRangeAndStaIDRange",
    _features("time_range", "station_level"): "ByTimeRangeAndStaLevels",
    _features("region_rect", "time"): "InRectByTime",
    _features("region_rect", "time_range"): "InRectByTimeRange",
    _features("region_region", "time"): "InRegionByTime",
    _features("region_region", "time_range"): "InRegionByTimeRange",
    _features("region_basin", "time"): "InBasinByTime",
    _features("region_basin", "time_range"): "InBasinByTimeRange",
}


_OBS_FILE_SUFFIXES = {
    _features(): "",
    _features("time"): "ByTime",
    _features("time_range"): "ByTimeRange",
    _features("station"): "ByStaID",
    _features("station_range"): "ByStaIDRange",
    _features("station_level"): "ByStaLevels",
    _features("time", "station"): "ByTimeAndStaID",
    _features("time", "station_range"): "ByTimeAndStaIDRange",
    _features("time_range", "station"): "ByTimeRangeAndStaID",
    _features("time_range", "station_range"): "ByTimeRangeAndStaIDRange",
    _features("time", "station_level"): "ByTimeAndStaLevels",
    _features("time_range", "station_level"): "ByTimeRangeAndStaLevels",
    _features("region_rect"): "InRect",
    _features("region_rect", "time"): "InRectByTime",
    _features("region_rect", "time_range"): "InRectByTimeRange",
    _features("region_region"): "InRegion",
    _features("region_region", "time"): "InRegionByTime",
    _features("region_region", "time_range"): "InRegionByTimeRange",
    _features("region_basin"): "InBasin",
    _features("region_basin", "time"): "InBasinByTime",
    _features("region_basin", "time_range"): "InBasinByTimeRange",
    _features("region_rect", "time", "station"): "InRectByTimeAndStaID",
    _features("region_rect", "time_range", "station"): "InRectByTimeRangeAndStaID",
    _features("region_region", "time", "station"): "InRegionByTimeAndStaID",
    _features("region_region", "time_range", "station"): "InRegionByTimeRangeAndStaID",
    _features("region_basin", "time", "station"): "InBasinByTimeAndStaID",
    _features("region_basin", "time_range", "station"): "InBasinByTimeRangeAndStaID",
}


def _obs_station_declarations(base: str) -> dict[frozenset[str], tuple[str, frozenset[str]]]:
    result = {}
    suffixes = _OBS_STATION_SUFFIXES if base == "getSurfEle" else _OBS_FILE_SUFFIXES
    for feature_set, suffix in suffixes.items():
        if any(name.startswith("region_") for name in feature_set):
            region_name = next(name for name in feature_set if name.startswith("region_"))
            condition_features = feature_set - {region_name}
            prefix = base + {"region_rect": "InRect", "region_region": "InRegion", "region_basin": "InBasin"}[region_name]
            if condition_features:
                condition_suffix = suffixes[condition_features].removeprefix("By")
                interface_id = prefix + "By" + condition_suffix
            else:
                interface_id = prefix
        else:
            interface_id = base + suffix
        required = {"dataCode"}
        if "time" in feature_set:
            required.add("times")
        if "time_range" in feature_set:
            required.add("timeRange")
        if "station" in feature_set:
            required.add("staIds")
        if "station_range" in feature_set:
            required.update(("minStaId", "maxStaId"))
        if "station_level" in feature_set:
            required.add("staLevels")
        if any(name.startswith("region_") for name in feature_set):
            if "region_rect" in feature_set:
                required.update(("minLat", "minLon", "maxLat", "maxLon"))
            else:
                required.add("adminCodes" if "region_region" in feature_set else "basinCodes")
        result[feature_set] = (interface_id, frozenset(required))
    return result


_OBS_GRID_DECLARATIONS = {
    # Only these two IDs exist in the 2026-10-07 SURF_API catalog.
    _features("time"): ("getSurfEleGridByTime", _features("dataCode", "time")),
    _features("region", "time"): ("getSurfEleGridInRectByTime", _features("dataCode", "time", "minLat", "minLon", "maxLat", "maxLon")),
}


_OBS_FILE_DECLARATIONS = {
    # Only these IDs exist in the 2026-10-07 SURF_API catalog.
    _features("time"): ("getSurfFileByTime", _features("dataCode", "times")),
    _features("time_range"): ("getSurfFileByTimeRange", _features("dataCode", "timeRange")),
    _features("station", "time_range"): (
        "getSurfFileByTimeRangeAndStaID",
        _features("dataCode", "timeRange", "staIds"),
    ),
}

_OBS_UPPER_FILE_DECLARATIONS = {
    # Only these IDs exist in the 2026-10-07 UPAR_API catalog.
    _features("time"): ("getUparFileByTime", _features("dataCode", "times")),
    _features("time_range"): ("getUparFileByTimeRange", _features("dataCode", "timeRange")),
    _features("station", "time"): (
        "getUparFileByTimeAndStaID", _features("dataCode", "times", "staIds")
    ),
    _features("station", "time_range"): (
        "getUparFileByTimeRangeAndStaID", _features("dataCode", "timeRange", "staIds")
    ),
}


_UPPER_SUFFIXES = {
    _features(): "",
    _features("time"): "ByTime",
    _features("time_range"): "ByTimeRange",
    _features("station"): "ByStaID",
    _features("station_range"): "ByStaIDRange",
    _features("station_level"): "ByStaLevels",
    _features("region"): "InRect",
    _features("region", "time"): "InRectByTime",
    _features("region", "time_range"): "InRectByTimeRange",
    _features("time", "station"): "ByTimeAndStaID",
    _features("time_range", "station"): "ByTimeRangeAndStaID",
    _features("time", "station_level"): "ByTimeAndStaLevels",
    _features("time_range", "station_level"): "ByTimeRangeAndStaLevels",
    _features("time", "level_press"): "ByTimeAndPress",
    _features("time", "level_height"): "ByTimeAndHeight",
    _features("time", "level_vertical"): "ByTimeAndVertical",
    _features("time", "station", "level_press"): "ByTimeAndStaIDAndPress",
}


def _upper_declarations(base: str) -> dict[frozenset[str], tuple[str, frozenset[str]]]:
    result = {}
    for feature_set, suffix in _UPPER_SUFFIXES.items():
        required = {"dataCode", "elements"}
        if "time" in feature_set:
            required.add("times")
        if "time_range" in feature_set:
            required.add("timeRange")
        if "station" in feature_set:
            required.add("staIds")
        if "station_range" in feature_set:
            required.update(("minStaId", "maxStaId"))
        if "station_level" in feature_set:
            required.add("staLevels")
        if "region" in feature_set:
            required.update(("minLat", "minLon", "maxLat", "maxLon"))
        if "level_press" in feature_set:
            required.add("pLayers")
        if "level_height" in feature_set:
            required.add("hLayers")
        if "level_vertical" in feature_set:
            required.add("verticals")
        result[feature_set] = (base + suffix, frozenset(required))
    return result


_DECLARATIONS = {
    "model_grid_forecast": {
        features: spec for features, spec in _model_grid_declarations("getNafpEleGrid").items()
        if spec[0] in _CATALOG_MODEL_GRID_IDS["model_grid_forecast"]
    },
    "model_grid_analysis": {
        features: spec for features, spec in _model_grid_declarations("getNafpAnaEleGrid").items()
        if spec[0] in _CATALOG_MODEL_GRID_IDS["model_grid_analysis"]
    },
    "model_point": {
        _features("time", "level", "valid_time", "point"): ("getNafpEleAtPointByTimeAndLevelAndValidtime", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel", "validTime", "latLons")),
        _features("time", "level", "valid_time_range", "point"): ("getNafpEleAtPointByTimeAndLevelAndValidtimeRange", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel", "minVT", "maxVT", "latLons")),
        _features("time", "level", "valid_time", "station"): ("getNafpEleByTimeAndLevelAndValidtimeAndStaID", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel", "validTime", "staIds")),
        _features("time", "level", "valid_time_range", "station"): ("getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID", _features("dataCode", "fcstEle", "time", "levelType", "fcstLevel", "minVT", "maxVT", "staIds")),
    },
    "model_file": _MODEL_FILE_DECLARATIONS,
    "obs_station": _obs_station_declarations("getSurfEle"),
    "obs_file": _OBS_FILE_DECLARATIONS,
    "obs_upper_file": _OBS_UPPER_FILE_DECLARATIONS,
    "obs_grid": _OBS_GRID_DECLARATIONS,
    # Exact IDs from the 2026-10-07 UPAR_API catalog. Other suffixes are not
    # service interfaces and must fail before a client request is made.
    "obs_upper": {
        features: spec for features, spec in _upper_declarations("getUparEle").items()
        if spec[0] in {
            "getUparEleByTime", "getUparEleByTimeRange",
            "getUparEleInRectByTime", "getUparEleInRectByTimeRange",
            "getUparEleByTimeAndStaID", "getUparEleByTimeRangeAndStaID",
            "getUparEleByTimeAndPress", "getUparEleByTimeAndHeight",
            "getUparEleByTimeAndVertical", "getUparEleByTimeAndStaIDAndPress",
        }
    },
    "obs_upper_gps": {
        features: spec for features, spec in _upper_declarations("getUparGpsEle").items()
        if spec[0] in {
            "getUparGpsEleInRectByTime", "getUparGpsEleByTimeAndStaID",
            "getUparGpsEleByTimeRangeAndStaID",
        }
    },
    "obs_upper_light": {
        _features("region", "time_range"): (
            "getUparLightEleInRectByTimeRange",
            _features("dataCode", "elements", "timeRange", "minLat", "minLon", "maxLat", "maxLon"),
        ),
    },
    "obs_upper_ard": {
        _features("time_range", "level_height_range"): (
            "getUparArdEleByTimeRangeAndHeightRange",
            _features("dataCode", "elements", "timeRange", "minFLayer", "maxFLayer"),
        ),
        _features("region", "time_range", "level_height_range"): (
            "getUparArdEleInRectByTimeRangeAndHeightRange",
            _features("dataCode", "elements", "timeRange", "minFLayer", "maxFLayer", "minLat", "minLon", "maxLat", "maxLon"),
        ),
    },
    "obs_station_latest": {
        _features(): ("getSurfLatestTime", _features("dataCode", "latestTime")),
    },
    "obs_file_latest": {
        _features(): ("getSurfLatestTime", _features("dataCode", "latestTime")),
    },
    "obs_upper_latest": {
        _features(): ("getUparLatestTime", _features("dataCode", "latestTime")),
    },
    "model_file_latest": {
        _features(): ("getNafpLatestTime", _features("dataCode", "latestTime")),
    },
}


INTERFACE_SPECS = tuple(
    spec
    for family, declarations in _DECLARATIONS.items()
    for spec in _make_specs(
        family,
        "file_list" if family in {"model_file", "obs_file", "obs_upper_file"}
        else "grid_array_2d" if family in {"model_grid_forecast", "model_grid_analysis", "obs_grid"}
        else "array_2d",
        declarations,
    )
)

_SPEC_INDEX = {(spec.family, spec.query_features): spec for spec in INTERFACE_SPECS}


def resolve_interface(
    family: str,
    query_features: Iterable[str],
    *,
    params: Mapping[str, object] | None = None,
) -> InterfaceSpec:
    """Resolve a high-level query by exact feature-set match.

    ``query_features`` is an internal normalized representation.  It is never
    interpreted as an interface-name fragment and cannot create new ids.
    """
    feature_set = frozenset(query_features)
    try:
        spec = _SPEC_INDEX[(family, feature_set)]
    except KeyError as exc:
        supported = sorted(
            ", ".join(sorted(item.query_features)) or "<none>"
            for item in INTERFACE_SPECS
            if item.family == family
        )
        if not supported:
            raise UnsupportedQueryError(f"unknown high-level interface family: {family}") from exc
        raise UnsupportedQueryError(
            f"unsupported query features for {family}: "
            f"{', '.join(sorted(feature_set)) or '<none>'}; "
            f"supported combinations: {'; '.join(supported)}"
        ) from exc

    return spec


__all__ = ["INTERFACE_SPECS", "InterfaceSpec", "UnsupportedQueryError", "resolve_interface"]
