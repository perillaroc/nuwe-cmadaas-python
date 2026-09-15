from typing import Union, Optional, Dict, List, TypedDict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from nuwe_cmadaas.util import (
    forecast_hours,
    get_region_params,
    normalize_level,
    time_filter_params,
    validate_level_pair,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.interfaces import resolve_interface


class InterfaceConfig(TypedDict):
    name: str
    element: Optional[str]
    region: Optional[str]
    time: Optional[str]
    level: Optional[str]
    valid_time: Optional[str]


def download_model_file(
        data_code: str,
        parameter: Optional[Union[str, List[str]]] = None,
        start_time: Optional[Union[pd.Interval, pd.Timestamp, datetime, List, pd.Timedelta, timedelta]] = None,
        forecast_time: Optional[Union[str, pd.Timedelta, timedelta]] = None,
        level_type: Optional[Union[str, int]] = None,
        level: Optional[Union[int, float]] = None,
        region: Optional[Dict] = None,
        data_type: Optional[str] = None,
        output_dir: Optional[Union[Path, str]] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
) -> Union[List[Path], MusicError]:
    validate_level_pair(level_type, level)

    interface_config = InterfaceConfig(
        name="getNafpFile",
        element=None,
        region=None,
        time=None,
        level=None,
        valid_time=None,
    )

    if output_dir is None:
        output_dir = "./"

    if data_type is None:
        data_type = "forecast"
    # data_type_mapper = {
    #     "forecast": "getNafpEleGrid",
    #     "analysis": "getNafpAnaEleGrid",
    # }
    # interface_config["name"] = data_type_mapper.get(data_type)

    params = {
        "dataCode": data_code,
    }

    if isinstance(parameter, str):
        params["fcstEle"] = parameter
        interface_config["element"] = "Element"
    elif isinstance(parameter, list):
        if not parameter or not all(isinstance(item, str) and item for item in parameter):
            raise ValueError("parameter must be a non-empty list of strings")
        params["elements"] = ".".join(parameter)
    elif parameter is not None:
        raise TypeError(f"unsupported parameter type: {type(parameter).__name__}")

    if level_type is not None:
        params["levelType"] = str(level_type)
        interface_config["level"] = "Level"
    if level is not None:
        params["fcstLevel"] = str(normalize_level(level))

    normalized_time, time_params = time_filter_params(
        start_time, field_name="start_time"
    )
    if normalized_time is not None and normalized_time.kind == "range":
        interface_config["time"] = "TimeRange"
    elif normalized_time is not None and normalized_time.kind in ("single", "multiple"):
        interface_config["time"] = "Time"
    elif normalized_time is not None and normalized_time.kind == "latest":
        interface_config["name"] = "getNafpLatestTime"
    params.update(time_params)
    if normalized_time is not None and normalized_time.kind == "latest":
        params.pop("elements", None)

    if forecast_time is not None:
        valid_time = forecast_hours(forecast_time)
        if parameter is None and level_type is None and level is None:
            # Typically for NWP files which all fields of one time step are stored together.
            # There is no getNafpFileByTimeAndValidtime interface.
            # So use getNafpFileByTime instead, and set valid time condition in eleValueRanges.
            params["eleValueRanges"] = f"Validtime_C:'{valid_time:03d}'"
        else:
            interface_config["valid_time"] = "Validtime"
            params["validTime"] = str(valid_time)

    if region is not None:
        get_region_params(region, params, interface_config)

    family = "model_file_latest" if interface_config["name"] == "getNafpLatestTime" else "model_file"
    interface_id = resolve_interface(
        family,
        _features_from_config(interface_config),
        params=params,
    ).interface_id
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_downFile(interface_id, params, file_dir=output_dir)

    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        music_error = MusicError(code=result.request.error_code, message=result.request.error_message)
        return music_error

    files_info = result.files_info
    file_list = []
    for f in files_info:
        file_list.append(Path(output_dir, f.file_name))

    return file_list


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    family = "model_file_latest" if interface_config["name"] == "getNafpLatestTime" else "model_file"
    return resolve_interface(family, _features_from_config(interface_config)).interface_id


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    if interface_config["element"] is not None:
        features.add("element")
    if interface_config["region"] is not None:
        features.add(
            "region" if interface_config["region"] == "Rect"
            else f"region_{interface_config['region'].lower()}"
        )
    if interface_config["time"] == "TimeRange":
        features.add("time_range")
    elif interface_config["time"] is not None:
        features.add("time")
    if interface_config["level"] is not None:
        features.add("level")
    if interface_config["valid_time"] is not None:
        features.add("valid_time")
    return frozenset(features)
