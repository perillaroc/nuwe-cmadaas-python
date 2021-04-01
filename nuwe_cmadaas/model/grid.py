from typing import Union, Optional, Dict
import pandas as pd
import xarray as xr

from nuwe_cmadaas._util import _get_time_string, _get_client
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.station._retrieve import _get_region_params


def retrieve_model_grid(
        data_type: str,
        parameter: str,
        start_time: pd.Timestamp,
        forecast_time: Union[str, pd.Timedelta],
        level_type: Union[str, int],
        level: Union[int, float],
        region: Dict = None,
        config_file: Optional[str] = None
) -> xr.DataArray:
    interface_config = {
        "name": "getNafpEleGrid",
        "region": None,
        "time": "Time",
        "level": "Level",
        "valid_time": "Validtime"
    }

    params = {
        "dataCode": data_type,
        "fcstEle": parameter,
        "levelType": str(level_type),
        "fcstLevel": str(level)
    }

    time = _get_time_string(start_time)
    params["time"] = time

    if isinstance(forecast_time, str):
        forecast_time = pd.to_timedelta(forecast_time)
    valid_time = int(forecast_time / pd.Timedelta(hours=1))
    params["validTime"] = str(valid_time)

    if region is not None:
        _get_region_params(region, params, interface_config)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    client = _get_client(config_file)
    result = client.callAPI_to_gridArray2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")

    field = result.to_xarray()
    return field


def _get_interface_id(interface_config: Dict) ->str:
    interface_id = interface_config["name"]

    region_part = interface_config["region"]
    if region_part is not None:
        interface_id += "In" + region_part

    condition_part = "And".join(filter(None, [
        interface_config["time"],
        interface_config["level"],
        interface_config["valid_time"]
    ]))
    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    return interface_id