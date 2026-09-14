from typing import Union, Optional, Dict, List, Tuple, TypedDict
from pathlib import Path

import pandas as pd

from nuwe_cmadaas.util import (
    forecast_hour_range,
    forecast_hours,
    get_time_string,
    validate_lat_lon_pair,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger


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
        start_time: pd.Timestamp,
        forecast_time: Union[str, pd.Timedelta, Tuple],
        level_type: Union[str, int],
        level: Union[int, float],
        point: Union[Tuple[float, float], List[Tuple[float, float]]] = None,
        station: Union[List[str], str] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
) -> Union[pd.DataFrame, MusicError]:
    if level_type is None or level is None:
        raise ValueError("level_type and level must be provided together")
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
        "fcstLevel": str(level)
    }

    time = get_time_string(start_time)
    params["time"] = time

    if isinstance(forecast_time, (str, pd.Timedelta)):
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

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_array2D(interface_id, params)

    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        music_error = MusicError(code=result.request.error_code, message=result.request.error_message)
        return music_error

    df = result.to_pandas()
    return df


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    interface_id = interface_config["name"]

    point_part = interface_config["point"]
    if point_part is not None:
        interface_id += "At" + point_part

    condition_part = "And".join(filter(None, [
        interface_config["time"],
        interface_config["level"],
        interface_config["valid_time"],
        interface_config["station"]
    ]))
    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    return interface_id


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
    interface_config["station"] = "StaID"
    if isinstance(station, list):
        if not station:
            raise ValueError("station must not be an empty list")
        if not all(isinstance(item, str) and item for item in station):
            raise TypeError("station must contain non-empty strings")
        params["staIds"] = ",".join(station)
    elif isinstance(station, str):
        if not station:
            raise ValueError("station must not be empty")
        params["staIds"] = station
    else:
        raise TypeError(f"station type is not support: {type(station)}")
