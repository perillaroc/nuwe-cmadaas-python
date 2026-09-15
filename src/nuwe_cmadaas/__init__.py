from .music import (
    Array2D,
    GridArray2D,
    FilesInfo,
    FileInfo,
    GridScalar2D,
    GridVector2D,
    DataBlock,
    CMADaaSClient
)

from .config import CMADaasConfig

from .obs import (
    retrieve_obs_station,
    retrieve_obs_grid,
    retrieve_obs_upper_air,
    download_obs_file,
    download_obs_upper_air_file,
)
from .model import (
    retrieve_model_point,
    retrieve_model_grid,
    download_model_file,
)
from .music import (
    CMADaaSError,
    CMADaaSAuthenticationError,
    CMADaaSConfigurationError,
    CMADaaSDecodeError,
    CMADaaSDownloadError,
    CMADaaSQueryError,
    CMADaaSRequestError,
    CMADaaSTransportError,
    MusicError,
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("nuwe-cmadaas")
except PackageNotFoundError:
    # package is not installed
    pass


__all__ = [
    "Array2D",
    "GridArray2D",
    "FilesInfo",
    "FileInfo",
    "GridScalar2D",
    "GridVector2D",
    "DataBlock",
    "CMADaaSClient",
    "CMADaasConfig",
    "MusicError",
    "CMADaaSError",
    "CMADaaSAuthenticationError",
    "CMADaaSConfigurationError",
    "CMADaaSDecodeError",
    "CMADaaSDownloadError",
    "CMADaaSQueryError",
    "CMADaaSRequestError",
    "CMADaaSTransportError",
    "retrieve_model_point",
    "retrieve_model_grid",
    "download_model_file",
    "retrieve_obs_station",
    "retrieve_obs_grid",
    "retrieve_obs_upper_air",
    "download_obs_file",
    "download_obs_upper_air_file",
]
