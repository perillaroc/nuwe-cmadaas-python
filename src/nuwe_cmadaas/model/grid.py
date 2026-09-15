from typing import Union, Optional, Dict, Literal, TypedDict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import xarray as xr

from nuwe_cmadaas.util import (
    forecast_hours,
    get_time_string,
    get_region_params,
    normalize_level,
    normalize_timestamp,
    validate_level_pair,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.interfaces import resolve_interface


class InterfaceConfig(TypedDict):
    name: str
    region: Optional[str]
    time: Optional[str]
    level: Optional[str]
    valid_time: Optional[str]
    number: Optional[str]


def retrieve_model_grid(
        data_code: str,
        parameter: str,
        start_time: Optional[Union[pd.Timestamp, datetime]] = None,
        forecast_time: Optional[Union[str, pd.Timedelta, timedelta]] = None,
        level_type: Optional[Union[str, int]] = None,
        level: Optional[Union[int, float]] = None,
        region: Optional[Dict] = None,
        number: Optional[int] = None,
        data_type: Optional[Literal["analysis", "forecast"]] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
) -> Union[xr.DataArray, MusicError]:
    """
    获取数值模式的二维网格数据

    Parameters
    ----------
    data_code
        CMADaaS 数据编码，例如 `NAFP_FOR_FTM_GRAPES_GFS_25KM_GLB` 表示“中国气象局全球天气模式CMA-GFS原始分辨率全球预报产品（0.25×0.25)”
    parameter
        要素名称
    start_time
        起报时间
    forecast_time
        预报时效，支持 ``pandas.Timedelta``、``datetime.timedelta`` 和可转换的字符串，例如 `"24h"`
    level_type
        层次类型
    level
        层次值
    region
        区域
    number
        集合预报成员编号
    data_type
        数据类型，预报场 (`forecast`) 或者分析场 (`analysis`)
    config
        配置，配置对象或配置文件路径。默认自动查找配置文件
    client
        客户端对象，默认新建。如果设置，则直接使用该对象，会导致 config 参数被忽略

    Returns
    -------
    Union[xr.DataArray, MusicError]
        检索成功返回 ``xarray.DataArray`` 格式的要素场，检索失败返回包含错误信息的 ``MusicError`` 对象。
    """
    if data_type is None:
        data_type = "forecast"
    data_type_mapper = {
        "forecast": "getNafpEleGrid",
        "analysis": "getNafpAnaEleGrid",
    }
    if data_type not in data_type_mapper:
        allowed = ", ".join(sorted(data_type_mapper))
        raise ValueError(f"data_type must be one of {allowed}; got {data_type!r}")
    validate_level_pair(level_type, level)

    interface_config = InterfaceConfig(
        name="getNafpEleGrid",
        region=None,
        time=None,
        level=None,
        valid_time=None,
        number=None,
    )

    interface_config["name"] = data_type_mapper[data_type]

    params = {
        "dataCode": data_code,
        "fcstEle": parameter,
    }

    if level_type is not None:
        params["levelType"] = str(level_type)
        interface_config["level"] = "Level"

    if level is not None:
        params["fcstLevel"] = str(normalize_level(level))

    if start_time is not None:
        interface_config["time"] = "Time"
        time = get_time_string(normalize_timestamp(start_time, "start_time"))
        params["time"] = time

    if forecast_time is not None:
        interface_config["valid_time"] = "Validtime"
        valid_time = forecast_hours(forecast_time)
        params["validTime"] = str(valid_time)

    if region is not None:
        get_region_params(region, params, interface_config)

    if number is not None:
        interface_config["number"] = "FcstMember"
        params["fcstMember"] = number

    spec = resolve_interface(
        f"model_grid_{data_type}",
        _features_from_config(interface_config),
        params=params,
    )
    interface_id = spec.interface_id
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_gridArray2D(interface_id, params)

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

    field = result.to_xarray()
    return field


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    """
    根据接口各组成部分的名称返回接口的名称

    Parameters
    ----------
    interface_config
        接口各组成部分的名称

        .. code-block:: python

            interface_config = {
                "name": "getNafpEleGrid",
                "region": "Rect",
                "time": "Time",
                "level": "Level",
                "valid_time": "Validtime",
                "number": "FcstMember",
            }

    Returns
    -------
    str
        拼接后的 CMADaaS 接口名称

    Examples
    --------
    按起报时间、预报层次、预报时效检索预报要素场

    >>> _get_interface_id(
    ...     interface_config={
    ...         "name": "getNafpEleGrid",
    ...         "region": None,
    ...         "time": "Time",
    ...         "level": "Level",
    ...         "valid_time": "Validtime",
    ...         "number": None
    ...     }
    ... )
    getNafpEleGridByTimeAndLevelAndValidtime

    按经纬范围、起报时间、预报层次、预报时效、集合预报成员检索预报要素场

    >>> _get_interface_id(
    ...     interface_config={
    ...         "name": "getNafpEleGrid",
    ...         "region": "Rect",
    ...         "time": "Time",
    ...         "level": "Level",
    ...         "valid_time": "Validtime",
    ...         "number": "FcstMember"
    ...     }
    ... )
    getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember

    """
    family = "model_grid_analysis" if interface_config["name"] == "getNafpAnaEleGrid" else "model_grid_forecast"
    return resolve_interface(family, _features_from_config(interface_config)).interface_id


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    if interface_config["region"] is not None:
        features.add(
            "region" if interface_config["region"] == "Rect"
            else f"region_{interface_config['region'].lower()}"
        )
    if interface_config["time"] is not None:
        features.add("time")
    if interface_config["level"] is not None:
        features.add("level")
    if interface_config["valid_time"] is not None:
        features.add("valid_time")
    if interface_config["number"] is not None:
        features.add("number")
    return frozenset(features)
