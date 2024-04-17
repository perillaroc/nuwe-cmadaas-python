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

from nuwe_cmadaas.config import load_cmadaas_config, CMADaasConfig
from nuwe_cmadaas._log import logger


def create_client(config: Optional[Union[CMADaasConfig, str, Path]]) -> CMADaaSClient:
    """
    从配置中创建客户端 CMADaaSClient

    Parameters
    ----------
    config
        配置，配置对象或配置文件路径

    Returns
    -------
    CMADaaSClient
        CMADaaS 访问客户端
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
    if client is None:
        cmadaas_client = create_client(config)
    else:
        if config is not None:
            logger.warning("client is set, use client in argument, config is ignored.")
        cmadaas_client = client
    return cmadaas_client
