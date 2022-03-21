from typing import Union, List, Dict, Tuple
from pathlib import Path

import pandas as pd

from nuwe_cmadaas._log import logger
from nuwe_cmadaas._util import (
    _get_client,
    _get_time_string,
    _get_time_range_string
)

from nuwe_cmadaas.dataset import load_dataset_config
from ._util import _get_interface_id, _get_region_params


def retrieve_obs_station(
        data_code: str = "SURF_CHN_MUL_HOR",
        elements: str = None,
        time: Union[pd.Interval, pd.Timestamp, List, pd.Timedelta] = None,
        station: Union[str, List, Tuple] = None,
        region=None,
        station_level: Union[str, List[str]] = None,
        order: str = "Station_ID_d:asc",
        count: int = None,
        config_file: Union[str, Path] = None,
        **kwargs,
) -> pd.DataFrame:
    """
    检索地面站点观测数据资料。

    对应 CMADaaS 中以 `getSurfEle` 开头的一系列数据接口

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

    - 流域

    .. code-block:: python

        {
            "type": "basin",
            "basin_codes": "CJLY"
        }

    - 地区

    .. code-block:: python

        {
            "type": "region",
            "admin_codes": "110000"
        }

    Parameters
    ----------
    data_code
        数据种类，即 CMADaaS 中的资料代码
    elements
        要素字段代码，以逗号分隔
    time
        时间筛选条件，支持单个时间，时间列表，时间段和时间间隔

        - 时间对象：``pd.Timestamp`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``typing.List[pd.Timestamp]`` 类型，多个时间列表，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：``pd.Timedelta`` 类型，用于获取地面资料最新时次 (getSurfLatestTime)，忽略其余筛选条件
    station
        站点筛选条件，支持字符串，列表和元组

        - 字符串：单个站点
        - 列表：多个站点
        - 元组：站点范围，二元组，第一个元素是起止站号 (minStaId)，第二个元素是终止站号 (maxStaId)
    region
        区域筛选条件：
            - 经纬度范围 (rect)
            - 流域 (basin)
            - 地区 (region)

    station_level
        台站级别：
            - 011: 国家基准气候站
            - 012: 基本气象站
            - 013: 一般气象站
    order
        排序字段
    count
        最大返回记录数，对应接口的 limitCnt 参数
    config_file
        配置文件路径
    kwargs
        其他需要传递给 MUSIC 接口的参数，例如：
            - eleValueRanges: 要素值范围
            - hourSeparate: 小时取整条件
            - minSeparate: 分钟取整条件

    Returns
    -------
    pd.DataFrame
        站点观测资料表格数据，列名为 elements 中的值
    """
    station_dataset_config = load_dataset_config("station")
    if elements is None:
        elements = station_dataset_config[data_code]["elements"]

    interface_config = {
        "name": "getSurfEle",
        "region": None,
        "time": None,
        "station": None,
    }

    params = {
        "dataCode": data_code,
        "elements": elements,
        "orderby": order,
    }

    if count is not None:
        params["limitCnt"] = count

    if isinstance(time, pd.Interval):
        interface_config["time"] = "TimeRange"
        params["timeRange"] = _get_time_range_string(time)
    elif isinstance(time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["times"] = _get_time_string(time)
    elif isinstance(time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([_get_time_string(t) for t in time])
    elif isinstance(time, pd.Timedelta):
        interface_config["name"] = "getSurfLatestTime"
        params["latestTime"] = str(int(time / pd.to_timedelta("1h")))
        del params["orderby"]
        del params["elements"]

    if isinstance(station, str or int):
        interface_config["station"] = "StaID"
        params["staIds"] = station
    elif isinstance(station, List):
        interface_config["station"] = "StaID"
        params["staIds"] = ",".join(station)
    elif isinstance(station, Tuple):
        interface_config["station"] = "StaIdRange"
        params["minStaId"] = station[0]
        params["maxStaId"] = station[1]

    if region is not None:
        _get_region_params(region, params, interface_config)

    if station_level is not None:
        del params["orderby"]

    if isinstance(station_level, str):
        params["staLevels"] = station_level
        if interface_config["station"] is None:
            interface_config["station"] = "StaLevels"
    elif isinstance(station_level, List):
        params["staLevels"] = ",".join(station_level)
        if interface_config["station"] is None:
            interface_config["station"] = "StaLevels"

    params.update(**kwargs)

    interface_id = _get_interface_id(interface_config)
    logger.info(f"interface_id: {interface_id}")

    client = _get_client(config_file)
    result = client.callAPI_to_array2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")

    df = result.to_pandas()
    return df
