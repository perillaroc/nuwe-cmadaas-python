from typing import Union, List, Optional
from pathlib import Path

import pandas as pd
import xarray as xr

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_client,
    get_time_string,
    get_time_range_string
)

from ._util import _get_interface_id, _get_region_params


def retrieve_obs_grid(
        data_code: str,
        parameter: str = None,
        time: Union[pd.Interval, pd.Timestamp, List, pd.Timedelta] = None,
        region=None,
        order: str = None,
        config_file: Union[str, Path] = None,
        **kwargs,
) -> xr.DataArray:
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
    time:
        时间筛选条件，支持单个时间，时间列表，时间段和时间间隔

        - 时间对象：``pd.Timestamp`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``typing.List[pd.Timestamp]`` 类型，多个时间列表，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：``pd.Timedelta`` 类型，用于获取地面资料最新时次 (getSurfLatestTime)，忽略其余筛选条件
    region
        区域筛选条件：
            - 经纬度范围 (rect)
    order
        排序字段
    config_file
        配置文件路径
    kwargs
        其他需要传递给 MUSIC 接口的参数

    Returns
    -------
    xr.DataArray
    """
    interface_config = {
        "name": "getSurfEleGrid",
        "region": None,
        "time": None,
    }

    params = {
        "dataCode": data_code,
    }

    if isinstance(parameter, str):
        params["fcstEle"] = parameter

    if order is not None:
        params["orderby"] = order

    if isinstance(time, pd.Interval):
        interface_config["time"] = "TimeRange"
        params["timeRange"] = get_time_range_string(time)
    elif isinstance(time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["time"] = get_time_string(time)
    elif isinstance(time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([get_time_string(t) for t in time])
    elif isinstance(time, pd.Timedelta):
        interface_config["name"] = "getSurfLatestTime"
        params["latestTime"] = str(int(time / pd.to_timedelta("1h")))
        del params["orderby"]
        del params["elements"]

    if region is not None:
        _get_region_params(region, params, interface_config)

    params.update(**kwargs)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    client = get_client(config_file)
    result = client.callAPI_to_gridArray2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")

    field = result.to_xarray()
    return field
