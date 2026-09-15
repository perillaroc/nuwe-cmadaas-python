from typing import Union, List, Dict, Tuple, Optional, TypedDict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_region_params,
    station_filter_params,
    time_filter_params,
    validate_count,
)
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import MusicError, CMADaaSClient, get_or_create_client
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.dataset import load_dataset_config
from nuwe_cmadaas.interfaces import resolve_interface

from .util import InterfaceConfig


def retrieve_obs_station(
        data_code: str = "SURF_CHN_MUL_HOR",
        elements: Optional[str] = None,
        time: Optional[Union[pd.Interval, pd.Timestamp, datetime, List, pd.Timedelta, timedelta]] = None,
        station: Optional[Union[str, List, Tuple]] = None,
        region: Optional[Dict] = None,
        station_level: Optional[Union[str, List[str]]] = None,
        order: str = "Station_ID_d:asc",
        count: Optional[int] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
        **kwargs,
) -> Union[pd.DataFrame, MusicError]:
    """
    检索地面站点观测数据资料。
    对应 CMADaaS 中以 ``getSurfEle`` 开头的一系列地面资料接口。

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
        要素字段代码，以逗号分隔。如果为 ``None``，会自动从数据集配置文件 (默认为 ``nuwe_cmadaas/datasets/station.yaml``) 中查找对应资料的 ``elements`` 配置项。
    time
        时间筛选条件，支持单个时间，时间列表，时间段和时间间隔

        - 时间对象：``pd.Timestamp`` 或 ``datetime.datetime`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``list`` 或 ``tuple`` 类型，元素为 pandas 或标准库 datetime，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：``pd.Timedelta`` 或 ``datetime.timedelta`` 类型，用于获取地面资料最新时次 (getSurfLatestTime)，忽略其余筛选条件
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
    config
        配置。配置文件路径或配置对象
    client
        客户端对象。默认新建，如果设置则直接使用，忽略 config 参数
    kwargs
        其他需要传递给 MUSIC 接口的参数，例如：
            - eleValueRanges: 要素值范围
            - hourSeparate: 小时取整条件
            - minSeparate: 分钟取整条件

    Returns
    -------
    pd.DataFrame
        站点观测资料表格数据，列名为 ``elements`` 中的值
    """
    validate_count(count)

    station_dataset_config = load_dataset_config("station")
    if elements is None:
        elements = station_dataset_config[data_code]["elements"]

    interface_config = InterfaceConfig(
        name="getSurfEle",
        region=None,
        time=None,
        station=None,
        level=None,
    )

    params = {
        "dataCode": data_code,
        "elements": elements,
        "orderby": order,
    }

    if count is not None:
        params["limitCnt"] = count

    normalized_time, time_params = time_filter_params(time, single_key="times")
    if normalized_time is not None and normalized_time.kind == "range":
        interface_config["time"] = "TimeRange"
    elif normalized_time is not None and normalized_time.kind in ("single", "multiple"):
        interface_config["time"] = "Time"
    elif normalized_time is not None and normalized_time.kind == "latest":
        interface_config["name"] = "getSurfLatestTime"
        params.pop("orderby", None)
        params.pop("elements", None)
    params.update(time_params)

    normalized_station, station_params = station_filter_params(station)
    if normalized_station is not None and normalized_station.kind == "id":
        interface_config["station"] = "StaID"
    elif normalized_station is not None and normalized_station.kind == "ids":
        interface_config["station"] = "StaID"
    elif normalized_station is not None and normalized_station.kind == "range":
        interface_config["station"] = "StaIdRange"
    params.update(station_params)

    if region is not None:
        params, interface_config = get_region_params(region, params, interface_config)

    if station_level is not None:
        params.pop("orderby", None)

    if isinstance(station_level, str):
        if not station_level:
            raise ValueError("station_level must not be empty")
        params["staLevels"] = station_level
        if interface_config["station"] is None:
            interface_config["station"] = "StaLevels"
    elif isinstance(station_level, list):
        if not station_level or not all(isinstance(item, str) and item for item in station_level):
            raise ValueError("station_level must be a non-empty list of strings")
        params["staLevels"] = ",".join(station_level)
        if interface_config["station"] is None:
            interface_config["station"] = "StaLevels"
    elif station_level is not None:
        raise TypeError(f"unsupported station_level type: {type(station_level).__name__}")

    params.update(**kwargs)

    family = "obs_station_latest" if interface_config["name"] == "getSurfLatestTime" else "obs_station"
    interface_id = resolve_interface(
        family,
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


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    region = interface_config["region"]
    if region is not None:
        features.add({"Rect": "region_rect", "Region": "region_region", "Basin": "region_basin"}[region])
    if interface_config["time"] == "TimeRange":
        features.add("time_range")
    elif interface_config["time"] is not None:
        features.add("time")
    station = interface_config["station"]
    if station == "StaIdRange":
        features.add("station_range")
    elif station == "StaLevels":
        features.add("station_level")
    elif station is not None:
        features.add("station")
    return frozenset(features)
