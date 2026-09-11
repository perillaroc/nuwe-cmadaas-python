from typing import Union, Optional, Dict, List, TypedDict
from pathlib import Path

import pandas as pd

from nuwe_cmadaas.util import (
    get_time_string,
    get_time_range_string,
    get_region_params,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger


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
        start_time: Optional[Union[pd.Interval, pd.Timestamp, List, pd.Timedelta]] = None,
        forecast_time: Optional[Union[str, pd.Timedelta]] = None,
        level_type: Optional[Union[str, int]] = None,
        level: Optional[Union[int, float]] = None,
        region: Optional[Dict] = None,
        data_type: Optional[str] = None,
        output_dir: Optional[Union[Path, str]] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
) -> Union[List[Path], MusicError]:
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
    elif isinstance(parameter, List):
        params["elements"] = ".".join(parameter)

    if level_type is not None:
        params["levelType"] = str(level_type)
        interface_config["level"] = "Level"
    if level is not None:
        params["fcstLevel"] = str(level)

    if isinstance(start_time, pd.Interval):
        interface_config["time"] = "TimeRange"
        params["timeRange"] = get_time_range_string(start_time)
    elif isinstance(start_time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["time"] = get_time_string(start_time)
    elif isinstance(start_time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([get_time_string(t) for t in start_time])
    elif isinstance(start_time, pd.Timedelta):
        interface_config["name"] = "getNafpLatestTime"
        params["latestTime"] = str(int(start_time / pd.to_timedelta("1h")))
        # del params["orderby"]
        del params["elements"]

    if forecast_time is not None:
        if isinstance(forecast_time, str):
            forecast_time = pd.to_timedelta(forecast_time)
        valid_time = int(forecast_time / pd.Timedelta(hours=1))
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

    interface_id = _get_interface_id(interface_config)
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
    interface_id = interface_config["name"]

    region_part = interface_config["region"]
    if region_part is not None:
        interface_id += "In" + region_part

    condition_part = "And".join(filter(None, [
        interface_config["element"],
        interface_config["time"],
        interface_config["level"],
        interface_config["valid_time"]
    ]))
    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    return _fix_interface_id(interface_id)


def _fix_interface_id(interface_id: str) -> str:
    fix_mapper = {
        "getNafpFileByElementAndTimeRangeAndLevel": "getNafpFileByElementAndTimeRange",
        "getNafpFileByElementAndTimeAndLevel": "getNafpFileByElementAndTime",
    }
    return fix_mapper.get(interface_id, interface_id)
