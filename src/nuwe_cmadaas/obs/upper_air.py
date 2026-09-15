from typing import List, Tuple, Dict, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_region_params,
    normalize_level,
    station_filter_params,
    time_filter_params,
    validate_count,
    validate_level_pair,
)
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import get_or_create_client, CMADaaSClient, MusicError
from nuwe_cmadaas.dataset import load_dataset_config
from nuwe_cmadaas.interfaces import resolve_interface

from .util import _fix_params, InterfaceConfig
from .file import download_obs_file


def retrieve_obs_upper_air(
        data_code: str = "UPAR_GLB_MUL_FTM",
        elements: Optional[str] = None,
        time: Optional[Union[pd.Interval, pd.Timestamp, datetime, List, pd.Timedelta, timedelta]] = None,
        level_type: Optional[Union[str, Tuple[str]]] = None,
        level: Optional[Union[float, int, List[Union[float, int]], Tuple]] = None,
        station: Optional[Union[str, int, List, Tuple]] = None,
        region: Optional[Dict] = None,
        station_level: Optional[Union[str, List[str]]] = None,
        order: Optional[str] = None,
        count: Optional[int] = None,
        interface_data_type: Optional[str] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        **kwargs,
) -> Union[pd.DataFrame, MusicError]:
    """
    检索高空观测数据资料。

    对应 CMADaaS 中以 `getUparEle` 开头的一系列数据接口

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
    data_code:
        数据种类，即 CMADaaS 中的资料代码
    elements:
        要素字段代码，以逗号分隔
    time:
        时间筛选条件，支持单个时间，时间列表，时间段和时间间隔

        - 时间对象：``pd.Timestamp`` 或 ``datetime.datetime`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``list`` 或 ``tuple`` 类型，元素为 pandas 或标准库 datetime，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：``pd.Timedelta`` 或 ``datetime.timedelta`` 类型，用于获取地面资料最新时次 (getSurfLatestTime)，忽略其余筛选条件
    level_type:
        层次类型

        - pl: 气压层
        - gh/hgt: 位势高度
        - vertical: 垂直探测仪一，例如 4096 表示湿度特征层
        - fl/flight_level: 飞行高度
    level:
        层次
    station:
        站点筛选条件，支持字符串，列表和元组

        - 字符串：单个站点
        - 列表：多个站点
        - 元组：站点范围，二元组，第一个元素是起止站号 (minStaId)，第二个元素是终止站号 (maxStaId)
    region:
        区域筛选条件：
            - 经纬度范围 (rect)
            - 流域 (basin)
            - 地区 (region)

    station_level:
        台站级别：
            - 011: 国家基准气候站
            - 012: 基本气象站
            - 013: 一般气象站
    order:
        排序字段
    count:
        最大返回记录数，对应接口的 limitCnt 参数
    interface_data_type:
        资料类型，默认自动生成，或使用 datasets 配置文件中配置的 interface_data_type 字段
    config:
        配置。配置文件路径或配置对象
    client:
        客户端对象，默认新建。如果设置则直接使用，忽略 config 参数
    kwargs:
        其他需要传递给 MUSIC 接口的参数，例如：
            - eleValueRanges: 要素值范围
            - hourSeparate: 小时取整条件
            - minSeparate: 分钟取整条件

    Returns
    -------
    pd.DataFrame or MusicError
        检索成功返回高空观测资料表格数据，列名为 elements 中的值。
        检索失败返回错误对象 ``MusicError``
    """
    validate_count(count)
    validate_level_pair(level_type, level)

    upper_dataset_config = load_dataset_config("upper_air")
    if elements is None:
        elements = upper_dataset_config[data_code]["elements"]

    interface_config = InterfaceConfig(
        name="getUparEle",
        region=None,
        time=None,
        station=None,
        level=None,
    )

    if (
            interface_data_type is None
            and data_code in upper_dataset_config
            and "interface_data_type" in upper_dataset_config[data_code]
    ):
        interface_data_type = upper_dataset_config[data_code]["interface_data_type"]
    if interface_data_type is not None:
        interface_config["name"] = f"get{interface_data_type}Ele"

    params = {
        "dataCode": data_code,
        "elements": elements,
    }

    if order is not None:
        params["orderby"] = order
    if data_code in upper_dataset_config and "order_by" in upper_dataset_config[data_code]:
        params["orderby"] = upper_dataset_config[data_code]["order_by"]

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

    _get_level_params(
        level=level,
        level_type=level_type,
        interface_config=interface_config,
        params=params
    )

    normalized_station, station_params = station_filter_params(station)
    if normalized_station is not None and normalized_station.kind == "id":
        interface_config["station"] = "StaID"
    elif normalized_station is not None and normalized_station.kind == "ids":
        interface_config["station"] = "StaID"
    elif normalized_station is not None and normalized_station.kind == "range":
        interface_config["station"] = "StaIdRange"
    params.update(station_params)

    if region is not None:
        get_region_params(region, params, interface_config)

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

    family = {
        "getUparEle": "obs_upper",
        "getUparGpsEle": "obs_upper_gps",
        "getUparLightEle": "obs_upper_light",
        "getUparArdEle": "obs_upper_ard",
        "getSurfLatestTime": "obs_upper_latest",
    }.get(interface_config["name"])
    if family is None:
        raise ValueError(
            f"unregistered high-level upper-air interface: {interface_config['name']}"
        )
    interface_id = resolve_interface(
        family,
        _features_from_config(interface_config),
        params=params,
    ).interface_id
    logger.info(f"interface_id: {interface_id}")

    params = _fix_params(interface_id, params)

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_array2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        music_error = MusicError(code=result.request.error_code, message=result.request.error_message)
        return music_error

    df = result.to_pandas()
    return df


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    region = interface_config["region"]
    if region is not None:
        features.add(
            "region" if region == "Rect" else f"region_{region.lower()}"
        )
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
    level = interface_config["level"]
    if level == "Press":
        features.add("level_press")
    elif level == "Height":
        features.add("level_height")
    elif level == "Vertical":
        features.add("level_vertical")
    elif level is not None:
        features.add("level")
    return frozenset(features)


def download_obs_upper_air_file(
        data_code: str,
        elements: str = None,
        time: Union[pd.Interval, pd.Timestamp, List, pd.Timedelta] = None,
        station: Union[str, List, Tuple] = None,
        order: str = None,
        count: int = None,
        output_dir: str = "./",
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        **kwargs,
) -> Union[List, MusicError]:
    interface_data_type = "Upar"
    result = download_obs_file(
        data_code=data_code,
        elements=elements,
        time=time,
        station=station,
        order=order,
        count=count,
        output_dir=output_dir,
        interface_data_type=interface_data_type,
        config=config,
        client=client,
        **kwargs
    )
    return result


def _get_level_params(
        level_type,
        level,
        interface_config: InterfaceConfig,
        params: Dict
) -> Tuple[InterfaceConfig, Dict]:
    if level is None:
        return interface_config, params

    def get_level(level_type: str, level):
        level = normalize_level(level)
        if level_type == "pl":
            interface_level_config = "Press"
            level_params_name = "pLayers"
        elif level_type in ("hgt", "gh"):
            interface_level_config = "Height"
            level_params_name = "hLayers"
        elif level_type == "vertical":
            interface_level_config = "Vertical"
            level_params_name = "verticals"
        elif level_type in ("fl", "flight_height"):
            interface_level_config = "Height"
            interface_config["name"] = "getUparArdEle"
            level_params_name = "fLayer"
        else:
            raise ValueError(f"level_type is not supported: {level_type}")

        level_params = dict()
        if isinstance(level, (list, tuple)):
            level_params[level_params_name] = ",".join(str(item) for item in level)
        elif isinstance(level, pd.Interval):
            level_params[f"min{level_params_name.upper()}"] = level.left
            level_params[f"max{level_params_name.upper()}"] = level.right
            interface_level_config += "Range"
        else:
            level_params[level_params_name] = str(level)
        return interface_level_config, level_params

    if isinstance(level_type, str):
        interface_level_config, level_params = get_level(level_type, level)
    elif isinstance(level_type, tuple):
        if not isinstance(level, (list, tuple)):
            raise TypeError("level must be a sequence when level_type is a tuple")
        if len(level_type) == 0 or len(level_type) != len(level):
            raise ValueError("level_type and level must contain the same non-zero number of items")
        interface_level_config = []
        level_params = dict()
        for lt, l in zip(level_type, level):
            level_config, ps = get_level(lt, l)
            level_params.update(ps)
            interface_level_config.append(level_config)
        interface_level_config = "And".join(interface_level_config)
    else:
        raise TypeError(f"level_type is not supported: {level_type}")

    interface_config["level"] = interface_level_config
    params.update(level_params)
    return interface_config, params
