from typing import Union, Optional, Dict, List, TypedDict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from nuwe_cmadaas.util import (
    forecast_hours,
    get_region_params,
    normalize_level,
    time_filter_params,
    validate_level_pair,
)
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.music.errors import handle_response_error
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger
from nuwe_cmadaas.interfaces import UnsupportedQueryError, resolve_interface


class InterfaceConfig(TypedDict):
    name: str
    element: Optional[str]
    region: Optional[str]
    time: Optional[str]
    level: Optional[str]
    valid_time: Optional[str]


def download_model_file(
        data_code: str,
        parameter: Optional[Union[str, List[str]]] = None,
        start_time: Optional[Union[pd.Interval, pd.Timestamp, datetime, List, pd.Timedelta, timedelta]] = None,
        forecast_time: Optional[Union[str, pd.Timedelta, timedelta]] = None,
        level_type: Optional[Union[str, int]] = None,
        level: Optional[Union[int, float]] = None,
        region: Optional[Dict] = None,
        data_type: Optional[str] = None,
        output_dir: Optional[Union[Path, str]] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
        strict: bool = False,
        count: Optional[int] = None,
) -> Union[List[Path], MusicError]:
    """下载模式文件，成功返回实际写入磁盘的路径列表。

    Parameters
    ----------
    data_code:
        与具体文件接口和账号权限匹配的资料代码。
    parameter:
        字符串选择要素接口，生成 fcstEle，必须提供 level_type；可以不指定 level。
        非空字符串列表仅以点号连接为 elements，不选择要素接口，不等同于单要素查询。
    start_time:
        pandas/标准库时次生成 time，pd.Interval 生成 timeRange。
        时间列表生成 times，但当前接口必需 time，本地必需参数检查拒绝。
        相对 Timedelta 请求前拒绝；getNafpLatestTime 是 Datetime 表格，不能下载文件。
    forecast_time:
        非负整数小时的字符串或 pandas/标准库 timedelta，单时效，不支持范围。
        字符串要素查询生成 validTime；无要素、无层次时生成
        eleValueRanges="Validtime_C:'024'" 等过滤，仍使用时次/时间段文件接口。
    level_type:
        服务层次类型代码。字符串要素查询必需，即使未指定具体 level。
    level:
        单层值，须与 level_type 配对；目前具体层次仅登记要素加单时次组合。
    region:
        保留参数，但当前没有矩形、行政区或流域模式文件登记，查询前拒绝。
    data_type:
        兼容参数，当前不影响接口选择；analysis 不会切换到分析文件接口。
        必须通过具体 data_code 和接口能力区分资料，不能沿用格点的切换语义。
    output_dir:
        本地字符串或 Path 目录，None 使用当前目录；实际写文件时创建父目录。
    config:
        CedarKit 配置对象或 YAML 路径。
    client:
        已有 MUSIC 客户端，显式设置时优先于 config。
    strict:
        默认 False 时服务错误返回 MusicError；True 时抛结构化 CMADaaSError。
    count:
        正整数，仅时次/时间段非要素接口支持，生成字符串 limitCnt。
        不限制单文件或总字节数，其他五个要素接口传入此参数会请求前拒绝。

    Returns
    -------
    list[pathlib.Path] or MusicError
        成功返回已下载文件的本地 Path 列表，成功空清单返回 []；
        默认服务错误返回 MusicError，严格模式抛异常。本地参数错误直接抛异常。

    Notes
    -----
    当前七个文件下载登记与 latest-time 表格分开。目录创建依赖实际写入，
    已有同名文件默认覆盖；高层无本地 overwrite 或大小上限开关。
    单文件临时写入后替换，批量非事务，后续失败可能保留先前成功文件。
    """
    if level is not None or parameter is None:
        validate_level_pair(level_type, level)

    interface_config = InterfaceConfig(
        name="getNafpFile",
        element=None,
        region=None,
        time=None,
        level=None,
        valid_time=None,
    )

    if output_dir is None:
        output_dir = "./"

    if data_type is None:
        data_type = "forecast"
    # data_type_mapper = {
    #     "forecast": "getNafpEleGrid",
    #     "analysis": "getNafpAnaEleGrid",
    # }
    # interface_config["name"] = data_type_mapper.get(data_type)

    params = {
        "dataCode": data_code,
    }

    if isinstance(parameter, str):
        params["fcstEle"] = parameter
        interface_config["element"] = "Element"
    elif isinstance(parameter, list):
        if not parameter or not all(isinstance(item, str) and item for item in parameter):
            raise ValueError("parameter must be a non-empty list of strings")
        params["elements"] = ".".join(parameter)
    elif parameter is not None:
        raise TypeError(f"unsupported parameter type: {type(parameter).__name__}")

    if level_type is not None:
        params["levelType"] = str(level_type)
    if level is not None:
        params["fcstLevel"] = str(normalize_level(level))
        interface_config["level"] = "Level"

    normalized_time, time_params = time_filter_params(
        start_time, field_name="start_time"
    )
    if normalized_time is not None and normalized_time.kind == "range":
        interface_config["time"] = "TimeRange"
    elif normalized_time is not None and normalized_time.kind in ("single", "multiple"):
        interface_config["time"] = "Time"
    elif normalized_time is not None and normalized_time.kind == "latest":
        raise UnsupportedQueryError(
            "getNafpLatestTime returns a Datetime table and cannot download files; "
            "use CMADaaSClient.callAPI_to_array2D"
        )
    params.update(time_params)

    if forecast_time is not None:
        valid_time = forecast_hours(forecast_time)
        if parameter is None and level_type is None and level is None:
            # Typically for NWP files which all fields of one time step are stored together.
            # There is no getNafpFileByTimeAndValidtime interface.
            # So use getNafpFileByTime instead, and set valid time condition in eleValueRanges.
            params["eleValueRanges"] = f"Validtime_C:'{valid_time:03d}'"
        else:
            interface_config["valid_time"] = "Validtime"
            params["validTime"] = str(valid_time)

    if region is not None:
        get_region_params(region, params, interface_config)

    family = "model_file_latest" if interface_config["name"] == "getNafpLatestTime" else "model_file"
    spec = resolve_interface(
        family,
        _features_from_config(interface_config),
        params=params,
    )
    if count is not None:
        if type(count) is not int or count <= 0:
            raise ValueError("count must be a positive integer")
        if spec.interface_id not in {"getNafpFileByTime", "getNafpFileByTimeRange"}:
            raise ValueError("count is supported only for model file time queries")
        params["limitCnt"] = str(count)
    missing = spec.required_params.difference(params)
    if missing:
        raise ValueError(f"{spec.interface_id} requires parameters: {', '.join(sorted(missing))}")
    interface_id = spec.interface_id
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


def _get_interface_id(interface_config: InterfaceConfig) -> str:
    family = "model_file_latest" if interface_config["name"] == "getNafpLatestTime" else "model_file"
    return resolve_interface(family, _features_from_config(interface_config)).interface_id


def _features_from_config(interface_config: InterfaceConfig) -> frozenset[str]:
    features = set()
    if interface_config["element"] is not None:
        features.add("element")
    if interface_config["region"] is not None:
        features.add(
            "region" if interface_config["region"] == "Rect"
            else f"region_{interface_config['region'].lower()}"
        )
    if interface_config["time"] == "TimeRange":
        features.add("time_range")
    elif interface_config["time"] is not None:
        features.add("time")
    if interface_config["level"] is not None:
        features.add("level")
    if interface_config["valid_time"] is not None:
        features.add("valid_time")
    return frozenset(features)
