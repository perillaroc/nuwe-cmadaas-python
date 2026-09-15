from typing import Union, Optional, Dict, List, Tuple, TypedDict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from nuwe_cmadaas.util import (
    forecast_hour_range,
    forecast_hours,
    get_time_string,
    normalize_level,
    normalize_timestamp,
    station_filter_params,
    validate_lat_lon_pair,
    validate_level_pair,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.interfaces import resolve_interface


class InterfaceConfig(TypedDict):
    name: str
    point: Optional[str]
    time: str
    level: str
    valid_time: str
    station: Optional[str]


def retrieve_model_point(
        data_code: str,
        parameter: str,
        start_time: Union[pd.Timestamp, datetime],
        forecast_time: Union[str, pd.Timedelta, timedelta, Tuple],
        level_type: Union[str, int],
        level: Union[int, float],
        point: Union[Tuple[float, float], List[Tuple[float, float]]] = None,
        station: Union[List[str], str] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
) -> Union[pd.DataFrame, MusicError]:
    validate_level_pair(level_type, level)
    if point is not None and station is not None:
        raise ValueError("point and station are mutually exclusive")

    interface_config = InterfaceConfig(
        name="getNafpEle",
        point=None,
        time="Time",
        level="Level",
        valid_time="Validtime",
        station=None,
    )

    params = {
        "dataCode": data_code,
        "fcstEle": parameter,
        "levelType": str(level_type),
        "fcstLevel": str(normalize_level(level))
    }

    time = get_time_string(normalize_timestamp(start_time, "start_time"))
    params["time"] = time

    if isinstance(forecast_time, (str, pd.Timedelta, timedelta)):
        valid_time = forecast_hours(forecast_time)
        params["validTime"] = str(valid_time)
        interface_config["valid_time"] = "Validtime"
    elif isinstance(forecast_time, tuple):
        min_vt, max_vt = forecast_hour_range(forecast_time)
        interface_config["valid_time"] = "ValidtimeRange"
        params["minVT"] = str(min_vt)
        params["maxVT"] = str(max_vt)
    else:
        raise TypeError(
            "forecast_time must be a duration or a two-item duration tuple; "
            f"got {type(forecast_time).__name__}"
        )

    if point is not None:
        _get_point_params(point, params, interface_config)
    if station is not None:
        _get_station_params(station, params, interface_config)

    interface_id = resolve_interface(
        "model_point",
        _features_from_config(interface_config),
        params=params,
    ).interface_id
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_array2D(interface_id, params)

    if not result.ok:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        error = handle_response_error(
            result,
            interface_id=interface_id,
            params=params,
            strict=strict,
        )
        if error is not None:
            return error

    df = result.to_pandas()
    return df


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    return resolve_interface("model_point", _features_from_config(interface_config)).interface_id


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = {"time", "level"}
    if interface_config["point"] is not None:
        features.add("point")
    if interface_config["station"] is not None:
        features.add("station")
    if interface_config["valid_time"] == "ValidtimeRange":
        features.add("valid_time_range")
    else:
        features.add("valid_time")
    return frozenset(features)


def _get_point_params(
        point: Union[Tuple[float, float], List[Tuple[float, float]]],
        params: Dict,
        interface_config: Dict
):
    interface_config["point"] = "Point"
    if isinstance(point, tuple):
        validate_lat_lon_pair(point)
        params["latLons"] = f"{point[0]}/{point[1]}"
    elif isinstance(point, list):
        if not point:
            raise ValueError("point must not be an empty list")
        lat_lons = []
        for p in point:
            validate_lat_lon_pair(p, "point item")
            lat_lons.append(f"{p[0]}/{p[1]}")
        params["latLons"] = ",".join(lat_lons)
    else:
        raise TypeError("point must be a coordinate tuple or a non-empty list")


def _get_station_params(
        station: Union[List[str], str],
        params: Dict,
        interface_config: Dict
):
    normalized, station_params = station_filter_params(station)
    if normalized.kind == "range":
        raise TypeError("station range is not supported by retrieve_model_point")
    interface_config["station"] = "StaID"
    params.update(station_params)
