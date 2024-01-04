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

from .obs import retrieve_obs_station
from .model import (
    retrieve_model_point,
    retrieve_model_grid
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("nuwe-cmadaas")
except PackageNotFoundError:
    # package is not installed
    pass
