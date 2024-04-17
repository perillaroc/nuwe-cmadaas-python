from typing import Union, List, Optional, Dict
from pathlib import Path

import pandas as pd
import xarray as xr

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_time_string,
    get_time_range_string,
    get_region_params,
)
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import get_or_create_client, CMADaaSClient, MusicError

from .util import _get_interface_id, InterfaceConfig


def retrieve_obs_grid(
        data_code: str,
        parameter: Optional[str] = None,
        time: Optional[Union[pd.Interval, pd.Timestamp, List]] = None,
        region: Optional[Dict] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
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
        时间筛选条件，支持单个时间，时间列表，时间段和时间间隔

        - 时间对象：``pd.Timestamp`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``typing.List[pd.Timestamp]`` 类型，多个时间列表，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
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
    xr.DataArray or None
        检索成功则返回 ``xarray.DataArray`` 对象，否则返回 None
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

    if isinstance(time, pd.Interval):
        interface_config["time"] = "TimeRange"
        params["timeRange"] = get_time_range_string(time)
    elif isinstance(time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["time"] = get_time_string(time)
    elif isinstance(time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([get_time_string(t) for t in time])

    if region is not None:
        get_region_params(region, params, interface_config)

    params.update(**kwargs)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_gridArray2D(interface_id, params)

    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        music_error = MusicError(code=result.request.error_code, message=result.request.error_message)
        return music_error

    field = result.to_xarray()
    return field
