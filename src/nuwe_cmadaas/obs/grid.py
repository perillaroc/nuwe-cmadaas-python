from typing import Union, List, Optional, Dict
from datetime import datetime
from pathlib import Path

import pandas as pd
import xarray as xr

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_region_params,
    time_filter_params,
)
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import get_or_create_client, CMADaaSClient, MusicError
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.interfaces import resolve_interface

from .util import InterfaceConfig


def retrieve_obs_grid(
        data_code: str,
        parameter: Optional[str] = None,
        time: Optional[Union[pd.Interval, pd.Timestamp, datetime, List]] = None,
        region: Optional[Dict] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
        **kwargs,
) -> Union[xr.DataArray, MusicError]:
    """
    获取实况格点场要素

    对应 CMADaaS 中以 `getSurfEleGrid` 开头的一系列数据接口

    **区域筛选条件**

    - 经纬度范围

    .. code-block:: python

        {
            "type": "rect",
            "start_longitude": 115.7,
            "end_longitude": 117.4,
            "start_latitude": 41.6,
            "end_latitude": 39.4,
        }


    Parameters
    ----------
    data_code
        数据种类，即 CMADaaS 中的资料代码
    parameter
        要素字段代码
    time
        观测时次。当前登记支持时次查询及其矩形区域形式。

        - ``pd.Timestamp`` 或 ``datetime.datetime``：单个时次，对应原生 ``time`` 参数。
        - 非空时间列表或元组：本地映射为 ``times``，仍选择同一时次接口；
          是否支持多时次由资料决定，返回值不会自动增加时间维度。
        - ``pd.Interval`` 或省略时间：没有对应的登记组合，请求前抛 ``UnsupportedQueryError``。
        - ``pd.Timedelta`` 或 ``datetime.timedelta``：请求前抛 ``TypeError``，不执行 latest 查询。
    region
        区域筛选条件：
            - 经纬度范围 (rect)
    config
        配置。配置文件路径或配置对象
    client
        客户端对象，默认新建。如果设置则直接使用，忽略 config 参数
    kwargs
        其他需要传递给 MUSIC 接口的参数

    Returns
    -------
    xr.DataArray or MusicError
        检索成功返回 ``xarray.DataArray`` 对象，服务错误返回 ``MusicError``
    """
    interface_config = InterfaceConfig(
        name="getSurfEleGrid",
        region=None,
        time=None,
        level=None,
        station=None,
    )

    params = {
        "dataCode": data_code,
    }

    if isinstance(parameter, str):
        params["fcstEle"] = parameter

    normalized_time, time_params = time_filter_params(time)
    if normalized_time is not None and normalized_time.kind == "range":
        interface_config["time"] = "TimeRange"
    elif normalized_time is not None and normalized_time.kind in ("single", "multiple"):
        interface_config["time"] = "Time"
    elif normalized_time is not None and normalized_time.kind == "latest":
        raise TypeError("time timedelta is not supported by retrieve_obs_grid")
    params.update(time_params)

    if region is not None:
        get_region_params(region, params, interface_config)

    params.update(**kwargs)

    interface_id = resolve_interface(
        "obs_grid",
        _features_from_config(interface_config),
        params=params,
    ).interface_id
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


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    if interface_config["region"] is not None:
        features.add(
            "region" if interface_config["region"] == "Rect"
            else f"region_{interface_config['region'].lower()}"
        )
    if interface_config["time"] == "TimeRange":
        features.add("time_range")
    elif interface_config["time"] is not None:
        features.add("time")
    return frozenset(features)
