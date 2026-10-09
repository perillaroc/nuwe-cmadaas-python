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
    """检索模式经纬度点或站点的单层预报表格。

    Parameters
    ----------
    data_code:
        与具体点/站号接口及账号权限匹配的资料代码。
    parameter:
        服务要素代码，映射为 fcstEle；返回列名以响应为准，不保证等于此参数。
    start_time:
        pandas 或标准库起报时次，生成 time，不是预报有效时间。
    forecast_time:
        单时效用非负整数小时的字符串、pandas/标准库 timedelta，生成 validTime。
        范围用两个此类时效组成的元组，生成 minVT/maxVT；起点不得大于终点。
        范围不是绝对日期区间，也不承诺每个整数小时都有数据。
    level_type:
        与 level 配对的服务层次类型代码，生成 levelType；不使用 pl/gh 等别名映射。
    level:
        与 level_type 配对的单层值，生成 fcstLevel，单位按资料和层次定义。
    point:
        (纬度, 经度) 元组，或非空坐标对列表，生成 latLons。
        必须在 point/station 中选择一个，二者互斥；点值由服务返回，本地不插值。
    station:
        单站或非空站号列表，生成 staIds；元组表示站号范围，本入口不支持。
    config:
        CedarKit 配置对象或 YAML 路径。
    client:
        已有 MUSIC 客户端；显式设置时优先于 config。
    strict:
        默认 False 时服务错误返回 MusicError；True 时抛结构化 CMADaaSError。

    Returns
    -------
    pandas.DataFrame or MusicError
        成功返回响应列名及原始字符串值的表格；成功空响应可返回空表格。
        默认模式服务错误返回 MusicError，严格模式抛异常；本地错误直接抛异常。

    Notes
    -----
    登记点/站号各自与单时效/范围组成的四类查询，均需起报时次和层次。
    实际请求 time、level_type、level 与单时效 valid_time 等记录于 attrs；
    范围 minVT/maxVT 当前不自动写入 attrs，逐行时效以返回字段为准。
    不自动解析日期、数值、缺测标记或转换单位，也不保证单位写在 attrs 中。
    """
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
