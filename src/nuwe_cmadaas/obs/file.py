from typing import Union, List, Tuple, Optional, TypedDict
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
from nuwe_cmadaas.music import get_or_create_client, CMADaaSClient, MusicError
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface

from .util import InterfaceConfig


def download_obs_file(
        data_code: str,
        elements: str = None,
        time: Union[pd.Interval, pd.Timestamp, datetime, List, pd.Timedelta, timedelta] = None,
        station: Union[str, List, Tuple] = None,
        region=None,
        station_level: Union[str, List[str]] = None,
        order: str = None,
        count: int = None,
        output_dir: str = "./",
        interface_data_type: str = "Surf",
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
        **kwargs,
) -> Union[List[Path], MusicError]:
    """
    下载地面观测数据文件

    默认对应 CMADaaS 中以 `getSurfFile` 开头的一系列数据接口

    默认地面文件仅登记时次、时间段、时间段加站号三个组合。
    区域、站号范围及专用等级查询没有对应登记；相对时长查询在请求前拒绝，
    最新时次表格不能用作文件清单。参数能规范化不代表资料接口支持。

    Parameters
    ----------
    data_code:
        数据种类，即 CMADaaS 中的资料代码
    elements:
        要素字段代码，以逗号分隔
    time:
        时间筛选条件，支持时次、时间列表和时间段，组合须匹配当前登记。

        - 时间对象：``pd.Timestamp`` 或 ``datetime.datetime`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``list`` 或 ``tuple`` 类型，元素为 pandas 或标准库 datetime，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：不支持文件下载，请求前抛 UnsupportedQueryError；最新时次应作为表格查询
    station:
        站点筛选条件，支持字符串，列表和元组

        - 字符串：单个站点
        - 列表：多个站点
        - 元组：规范化为站点范围，但当前没有对应的文件下载登记组合

        默认地面站号查询必须配合时间段，不能使用单时次加站号。
    region:
        参数可规范化矩形、行政区和流域，但当前地面/高空文件均没有区域查询登记。

    station_level:
        可规范化为 staLevels，但没有专用等级文件接口登记；不能据签名认定支持。
    order:
        排序字段
    count:
        最大返回文件清单记录数，对应接口的 limitCnt 参数，不是本地下载字节上限。
    output_dir:
        本地字符串或 Path 目录。实际写文件时创建父目录；同名文件默认覆盖。
    interface_data_type:
        默认 Surf；Upar 用于高空文件包装路径，其已登记组合与地面不同。
    config:
        配置。配置文件路径或配置对象
    client:
        客户端对象，默认新建。如果设置，忽略 config 参数
    strict:
        默认 False 时服务错误返回 MusicError；True 时抛出结构化 CMADaaSError。
    kwargs:
        其他需要传递给 MUSIC 接口的参数，例如：
            - eleValueRanges: 要素值范围
            - hourSeparate: 小时取整条件
            - minSeparate: 分钟取整条件

    Returns
    -------
    list[pathlib.Path] or MusicError
        成功返回已下载文件的本地路径列表，成功空清单返回 []；
        默认模式的服务错误返回 MusicError，严格模式抛异常。

    Notes
    -----
    高层没有独立 overwrite 开关；该名称若通过 kwargs 传入，会成为服务参数。
    需要禁止覆盖时使用底层 callAPI_to_downFile(..., overwrite=False)。
    多文件下载不是事务，后续失败不会自动删除先前成功下载的文件。
    """
    validate_count(count)

    # if elements is None:
    #     elements = STATION_DATASETS[data_code]["elements"]

    interface_config = InterfaceConfig(
        name=f"get{interface_data_type}File",
        region=None,
        time=None,
        station=None,
        level=None,
    )

    params = {
        "dataCode": data_code,
    }

    if order is not None:
        params["orderby"] = order

    if elements is not None:
        params["elements"] = elements

    if count is not None:
        params["limitCnt"] = count

    normalized_time, time_params = time_filter_params(time, single_key="times")
    if normalized_time is not None and normalized_time.kind == "range":
        interface_config["time"] = "TimeRange"
    elif normalized_time is not None and normalized_time.kind in ("single", "multiple"):
        interface_config["time"] = "Time"
    elif normalized_time is not None and normalized_time.kind == "latest":
        raise UnsupportedQueryError(
            "getSurfLatestTime returns a Datetime table and cannot download files; "
            "use CMADaaSClient.callAPI_to_array2D"
        )
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

    if interface_config["name"] == "getUparFile":
        family = "obs_upper_file"
    elif interface_config["name"] == "getSurfFile":
        family = "obs_file"
    else:
        raise ValueError(
            f"unregistered high-level observation file interface: {interface_config['name']}"
        )
    interface_id = resolve_interface(
        family,
        _features_from_config(interface_config),
        params=params,
    ).interface_id
    logger.info(f"interface_id: {interface_id}")

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_downFile(interface_id, params, file_dir=output_dir)

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

    files_info = result.files_info
    file_list = []
    for f in files_info:
        file_list.append(Path(output_dir, f.file_name))

    return file_list


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
