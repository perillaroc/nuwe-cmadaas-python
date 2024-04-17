from typing import List, Tuple, Dict, Optional, Union
from pathlib import Path

import pandas as pd

from nuwe_cmadaas._log import logger
from nuwe_cmadaas.util import (
    get_time_string,
    get_time_range_string,
    get_region_params,
)
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import get_or_create_client, CMADaaSClient, MusicError
from nuwe_cmadaas.dataset import load_dataset_config

from ._util import _get_interface_id, _fix_params, InterfaceConfig
from ._file import download_obs_file


def retrieve_obs_upper_air(
        data_code: str = "UPAR_GLB_MUL_FTM",
        elements: Optional[str] = None,
        time: Optional[Union[pd.Interval, pd.Timestamp, List, pd.Timedelta]] = None,
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

        - 时间对象：``pd.Timestamp`` 类型，单个时间点，对应接口的 times 参数
        - 时间列表：``typing.List[pd.Timestamp]`` 类型，多个时间列表，对应接口的 times 参数
        - 时间段：``pd.Interval`` 类型，起止时间，定义区间端点是否闭合，对应接口的 timeRange 参数
        - 时间间隔：``pd.Timedelta`` 类型，用于获取地面资料最新时次 (getSurfLatestTime)，忽略其余筛选条件
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

    if isinstance(time, pd.Interval):
        interface_config["time"] = "TimeRange"
        params["timeRange"] = get_time_range_string(time)
    elif isinstance(time, pd.Timestamp):
        interface_config["time"] = "Time"
        params["times"] = get_time_string(time)
    elif isinstance(time, List):
        interface_config["time"] = "Time"
        params["times"] = ",".join([get_time_string(t) for t in time])
    elif isinstance(time, pd.Timedelta):
        interface_config["name"] = "getSurfLatestTime"
        params["latestTime"] = str(int(time / pd.to_timedelta("1h")))
        del params["orderby"]
        del params["elements"]

    _get_level_params(
        level=level,
        level_type=level_type,
        interface_config=interface_config,
        params=params
    )

    if isinstance(station, str) or isinstance(station, int):
        interface_config["station"] = "StaID"
        params["staIds"] = str(station)
    elif isinstance(station, List):
        interface_config["station"] = "StaID"
        params["staIds"] = ",".join(station)
    elif isinstance(station, Tuple):
        interface_config["station"] = "StaIdRange"
        params["minStaId"] = station[0]
        params["maxStaId"] = station[1]

    if region is not None:
        get_region_params(region, params, interface_config)

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

    params = _fix_params(interface_id, params)

    cmadaas_client = get_or_create_client(config, client)
    result = cmadaas_client.callAPI_to_array2D(interface_id, params)
    if result.request.error_code != 0:
        logger.warning(f"request error {result.request.error_code}: {result.request.error_message}")
        music_error = MusicError(code=result.request.error_code, message=result.request.error_message)
        return music_error

    df = result.to_pandas()
    return df


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
        if isinstance(level, List):
            level_params[level_params_name] = ",".join(level)
        if isinstance(level, pd.Interval):
            level_params[f"min{level_params_name.upper()}"] = level.left
            level_params[f"max{level_params_name.upper()}"] = level.right
            interface_level_config += "Range"
        else:
            params[level_params_name] = str(level)
        return interface_level_config, level_params

    if isinstance(level_type, str):
        interface_level_config, level_params = get_level(level_type, level)
    elif isinstance(level_type, Tuple):
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
