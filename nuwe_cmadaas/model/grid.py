from typing import Union, Optional, Dict, Literal, TypedDict
from pathlib import Path

import pandas as pd
import xarray as xr

from nuwe_cmadaas.util import get_time_string, get_region_params
from nuwe_cmadaas.music import MusicError, get_or_create_client, CMADaaSClient
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas._log import logger


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
        start_time: Optional[pd.Timestamp] = None,
        forecast_time: Optional[Union[str, pd.Timedelta]] = None,
        level_type: Optional[Union[str, int]] = None,
        level: Optional[Union[int, float]] = None,
        region: Optional[Dict] = None,
        number: Optional[int] = None,
        data_type: Optional[Literal["analysis", "forecast"]] = None,
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None,
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
        预报时效，``pandas.Timedelta`` 支持的字符串，例如 `"24h"`
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
    interface_config = InterfaceConfig(
        name="getNafpEleGrid",
        region=None,
        time=None,
        level=None,
        valid_time=None,
        number=None,
    )

    if data_type is None:
        data_type = "forecast"
    data_type_mapper = {
        "forecast": "getNafpEleGrid",
        "analysis": "getNafpAnaEleGrid",
    }
    interface_config["name"] = data_type_mapper.get(data_type)

    params = {
        "dataCode": data_code,
        "fcstEle": parameter,
    }

    if level_type is not None:
        params["levelType"] = str(level_type)
        interface_config["level"] = "Level"

    if level is not None:
        params["fcstLevel"] = str(level)

    if start_time is not None:
        interface_config["time"] = "Time"
        time = get_time_string(start_time)
        params["time"] = time

    if forecast_time is not None:
        interface_config["valid_time"] = "Validtime"
        if isinstance(forecast_time, str):
            forecast_time = pd.to_timedelta(forecast_time)
        valid_time = int(forecast_time / pd.Timedelta(hours=1))
        params["validTime"] = str(valid_time)

    if region is not None:
        get_region_params(region, params, interface_config)

    if number is not None:
        interface_config["number"] = "FcstMember"
        params["fcstMember"] = number

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
    interface_id = interface_config["name"]

    region_part = interface_config["region"]
    if region_part is not None:
        interface_id += "In" + region_part

    condition_part = "And".join(filter(None, [
        interface_config["time"],
        interface_config["level"],
        interface_config["valid_time"],
        interface_config["number"],
    ]))
    if len(condition_part) > 0:
        interface_id += "By" + condition_part

    return interface_id
