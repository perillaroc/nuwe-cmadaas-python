from typing import Union, Optional, Dict, List
import pathlib

import pandas as pd
import xarray as xr

from nuwe_cmadaas._util import _get_time_string, _get_client, _get_time_range_string
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.obs._station import _get_region_params


def download_model_file(
        data_code: str,
        parameter: Union[str, List[str]] = None,
        start_time: Union[pd.Interval, pd.Timestamp, List, pd.Timedelta] = None,
        forecast_time: Union[str, pd.Timedelta] = None,
        level_type: Union[str, int] = None,
        level: Union[int, float] = None,
        region: Dict = None,
        data_type: str = None,
        output_dir: Union[pathlib.Path, str] = None,
        config_file: Optional[str] = None
):
    interface_config = {
        "name": "getNafpFile",
        "element": None,
        "region": None,
        "time": None,
        "level": None,
        "valid_time": None
    }

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
        params["timeRange"] = _get_time_range_string(start_time)
    elif isinstance(start_time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["time"] = _get_time_string(start_time)
    elif isinstance(start_time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([_get_time_string(t) for t in start_time])
    elif isinstance(start_time, pd.Timedelta):
        interface_config["name"] = "getNafpLatestTime"
        params["latestTime"] = str(int(start_time / pd.to_timedelta("1h")))
        # del params["orderby"]
        del params["elements"]

    if forecast_time is not None:
        interface_config["valid_time"] = "Validtime"
        if isinstance(forecast_time, str):
            forecast_time = pd.to_timedelta(forecast_time)
        valid_time = int(forecast_time / pd.Timedelta(hours=1))
        params["validTime"] = str(valid_time)

    if region is not None:
        _get_region_params(region, params, interface_config)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    client = _get_client(config_file)
    result = client.callAPI_to_downFile(interface_id, params, file_dir=output_dir)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")

    files_info = result.files_info
    for file_info in files_info:
        logger.info(file_info.file_name)

    return


def _get_interface_id(interface_config: Dict) ->str:
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


def _fix_interface_id(interface_id):
    fix_mapper = {
        "getNafpFileByElementAndTimeRangeAndLevel": "getNafpFileByElementAndTimeRange",
        "getNafpFileByElementAndTimeAndLevel": "getNafpFileByElementAndTime",
    }
    return fix_mapper.get(interface_id, interface_id)
