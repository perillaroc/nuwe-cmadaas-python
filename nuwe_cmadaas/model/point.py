from typing import Union, Optional, Dict, List, Tuple
import pandas as pd

from nuwe_cmadaas._util import _get_time_string, _get_client
from nuwe_cmadaas._log import logger


def retrieve_model_point(
        data_type: str,
        parameter: str,
        start_time: pd.Timestamp,
        forecast_time: Union[str, pd.Timedelta, Tuple],
        level_type: Union[str, int],
        level: Union[int, float],
        point: Union[Tuple[float, float], List[Tuple[float, float]]] = None,
        station: Union[List[str], str] = None,
        config_file: Optional[str] = None
) -> pd.DataFrame:
    interface_config = {
        "name": "getNafpEle",
        "point": None,
        "time": "Time",
        "level": "Level",
        "valid_time": "Validtime",
        "station": None,
    }

    params = {
        "dataCode": data_type,
        "fcstEle": parameter,
        "levelType": str(level_type),
        "fcstLevel": str(level)
    }

    time = _get_time_string(start_time)
    params["time"] = time

    def _get_valid_time(f):
        if isinstance(f, str):
            f = pd.to_timedelta(f)
        return int(f / pd.Timedelta(hours=1))

    if isinstance(forecast_time, str or pd.Timedelta):
        valid_time = _get_valid_time(forecast_time)
        params["validTime"] = str(valid_time)
        interface_config["valid_time"] = "Validtime"
    elif isinstance(forecast_time, Tuple):
        interface_config["valid_time"] = "ValidtimeRange"
        params["minVT"] = str(_get_valid_time(forecast_time[0]))
        params["maxVT"] = str(_get_valid_time(forecast_time[1]))

    if point is not None:
        _get_point_params(point, params, interface_config)
    if station is not None:
        _get_station_params(station, params, interface_config)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    client = _get_client(config_file)
    result = client.callAPI_to_array2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")

    df = result.to_pandas()
    return df


def _get_interface_id(interface_config: Dict) ->str:
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
    if isinstance(point, Tuple):
        params["latLons"] = f"{point[0]}/{point[1]}"
    elif isinstance(point, List):
        lat_lons = []
        for p in point:
            lat_lons.append(f"{p[0]}/{p[1]}")
        params["latLons"] = ",".join(lat_lons)


def _get_station_params(
        station: Union[List[str], str],
        params: Dict,
        interface_config: Dict
):
    interface_config["station"] = "StaID"
    if isinstance(station, List):
        params["staIds"] = ",".join(station)
    elif isinstance(station, str):
        params["staIds"] = station
    else:
        raise TypeError(f"station type is not support: {type(station)}")
