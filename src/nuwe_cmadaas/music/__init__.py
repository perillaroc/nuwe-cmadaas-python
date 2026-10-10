from typing import Optional, Union
from pathlib import Path

from .data import (
    Array2D,
    GridArray2D,
    FilesInfo,
    FileInfo,
    GridScalar2D,
    GridVector2D,
    DataBlock,
    MusicError,
)

from .client import CMADaaSClient
from .errors import (
    CMADaaSError,
    CMADaaSAuthenticationError,
    CMADaaSConfigurationError,
    CMADaaSDecodeError,
    CMADaaSDownloadError,
    CMADaaSQueryError,
    CMADaaSRequestError,
    CMADaaSTransportError,
)

from nuwe_cmadaas.config import load_cmadaas_config, CMADaasConfig
from nuwe_cmadaas._log import logger


def create_client(config: Optional[Union[CMADaasConfig, str, Path]]) -> CMADaaSClient:
    """
    从配置中创建客户端 CMADaaSClient

    Parameters
    ----------
    config
        含 auth/server 的配置字典，或 CedarKit YAML 路径；该参数没有默认值，
        但可显式传 None 使用 YAML 的环境变量/用户默认文件查找规则。

    Returns
    -------
    CMADaaSClient
        本地初始化的客户端；创建不会请求服务。文件/解析/配置错误直接传播，
        不自动包装为 CMADaaSConfigurationError。
    """
    if isinstance(config, dict):
        cmadaas_config = config
    else:
        cmadaas_config = load_cmadaas_config(config)

    cmadaas_client = CMADaaSClient(config=cmadaas_config)
    return cmadaas_client


def get_or_create_client(
        config: Optional[Union[CMADaasConfig, str, Path]] = None,
        client: Optional[CMADaaSClient] = None
) -> CMADaaSClient:
    """Return an injected client, or create one from CedarKit configuration.

    Parameters
    ----------
    config : CMADaasConfig or str or pathlib.Path, optional
        Inner configuration dict or YAML path; None enables YAML discovery
        only when client is None.
    client : CMADaaSClient, optional
        When provided, returned unchanged without loading configuration.
        A simultaneous config value is ignored with a log warning.

    Returns
    -------
    CMADaaSClient
        Existing client or locally constructed client. This selection does
        not perform service requests or validate query parameters.
    """
    if client is None:
        cmadaas_client = create_client(config)
    else:
        if config is not None:
            logger.warning("client is set, use client in argument, config is ignored.")
        cmadaas_client = client
    return cmadaas_client


__all__ = [
    "Array2D",
    "DataBlock",
    "FileInfo",
    "FilesInfo",
    "GridArray2D",
    "GridScalar2D",
    "GridVector2D",
    "MusicError",
    "CMADaaSClient",
    "CMADaaSError",
    "CMADaaSAuthenticationError",
    "CMADaaSConfigurationError",
    "CMADaaSDecodeError",
    "CMADaaSDownloadError",
    "CMADaaSQueryError",
    "CMADaaSRequestError",
    "CMADaaSTransportError",
    "CMADaasConfig",
    "load_cmadaas_config",
    "create_client",
    "get_or_create_client",
]
