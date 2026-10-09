"""Factories for synthetic MUSIC protobuf responses and file content.

The factories deliberately construct protobuf messages in Python. They do not
contain recorded or transformed CMADaaS responses. This module is shared by
offline tests and documentation examples; it is not part of the installed
``nuwe_cmadaas`` package.
"""

from typing import Iterable, Optional, Sequence

import numpy as np

from nuwe_cmadaas.music import apiinterface_pb2 as pb
from nuwe_cmadaas.music.data import (
    Array2D,
    DataBlock,
    FilesInfo,
    GridArray2D,
    GridScalar2D,
    GridVector2D,
)


SYNTHETIC_STATION_ROWS = (
    ("FAKE001", "30.0", "110.0", "280.0"),
    ("FAKE002", "31.0", "111.0", "281.5"),
)
SYNTHETIC_STATION_ELEMENTS = ("Station_Id_C", "Lat", "Lon", "TEM")
SYNTHETIC_LATS = (30.0, 31.0)
SYNTHETIC_LONS = (110.0, 111.0, 112.0)
SYNTHETIC_GRID_VALUES = (
    (280.0, 280.5, 281.0),
    (281.5, 282.0, 282.5),
)
SYNTHETIC_ELEMENT_NAME = "synthetic_temperature"
SYNTHETIC_UNITS = "K"
SYNTHETIC_U_VALUES = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
SYNTHETIC_V_VALUES = (-1.0, -2.0, -3.0, -4.0, -5.0, -6.0)
SYNTHETIC_FILE_BYTES = b"FAKE"


def make_file_bytes() -> bytes:
    """Return the small file body described by the default ``FilesInfo``."""

    return SYNTHETIC_FILE_BYTES


def make_request_info(
    *,
    error_code: int = 0,
    error_message: str = "",
    row_count: int = 0,
    col_count: int = 0,
    request_elements: str = "synthetic_elements",
    request_params: str = "synthetic_params",
    request_time: str = "20260102000000",
    response_time: str = "20260102000001",
) -> pb.RequestInfo:
    """Create a deterministic request metadata message."""

    return pb.RequestInfo(
        errorCode=error_code,
        errorMessage=error_message,
        requestElems=request_elements,
        requestParams=request_params,
        requestTime=request_time,
        responseTime=response_time,
        rowCount=row_count,
        colCount=col_count,
    )


def make_array2d_content(
    *,
    rows: Optional[Sequence[Sequence[str]]] = None,
    element_names: Optional[Sequence[str]] = None,
    error_code: int = 0,
    error_message: str = "",
    row_count: Optional[int] = None,
    col_count: Optional[int] = None,
) -> bytes:
    """Serialize a synthetic ``RetArray2D`` response.

    ``row_count`` and ``col_count`` can be overridden independently to create
    malformed responses for parser tests.
    """

    rows = rows if rows is not None else SYNTHETIC_STATION_ROWS
    element_names = (
        element_names
        if element_names is not None
        else SYNTHETIC_STATION_ELEMENTS
    )
    rows = [tuple(str(value) for value in row) for row in rows]
    row_count = len(rows) if row_count is None else row_count
    col_count = len(element_names) if col_count is None else col_count

    message = pb.RetArray2D()
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=row_count,
            col_count=col_count,
        )
    )
    message.elementNames.extend(element_names)
    message.data.extend(value for row in rows for value in row)
    return message.SerializeToString()


def make_array2d_response(**kwargs) -> Array2D:
    """Build an :class:`Array2D` from a synthetic serialized response."""

    return Array2D.create_from_protobuf(make_array2d_content(**kwargs))


def make_grid_array2d_content(
    *,
    data: Optional[Iterable[float]] = None,
    lats: Optional[Sequence[float]] = None,
    lons: Optional[Sequence[float]] = None,
    start_lat: float = 30.0,
    start_lon: float = 110.0,
    end_lat: float = 31.0,
    end_lon: float = 112.0,
    lat_count: Optional[int] = None,
    lon_count: Optional[int] = None,
    lat_step: float = 1.0,
    lon_step: float = 1.0,
    units: str = SYNTHETIC_UNITS,
    element_name: str = SYNTHETIC_ELEMENT_NAME,
    error_code: int = 0,
    error_message: str = "",
) -> bytes:
    """Serialize a synthetic ``RetGridArray2D`` response."""

    lats = tuple(SYNTHETIC_LATS if lats is None else lats)
    lons = tuple(SYNTHETIC_LONS if lons is None else lons)
    lat_count = len(lats) if lat_count is None else lat_count
    lon_count = len(lons) if lon_count is None else lon_count
    if data is None:
        data = np.asarray(SYNTHETIC_GRID_VALUES).reshape(-1)

    message = pb.RetGridArray2D(
        startLat=start_lat,
        startLon=start_lon,
        endLat=end_lat,
        endLon=end_lon,
        latCount=lat_count,
        lonCount=lon_count,
        latStep=lat_step,
        lonStep=lon_step,
        units=units,
        userEleName=element_name,
    )
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=lat_count,
            col_count=lon_count,
        )
    )
    message.lats.extend(lats)
    message.lons.extend(lons)
    message.data.extend(float(value) for value in data)
    return message.SerializeToString()


def make_grid_array2d_response(**kwargs) -> GridArray2D:
    """Build a :class:`GridArray2D` from a synthetic serialized response."""

    return GridArray2D.create_from_protobuf(make_grid_array2d_content(**kwargs))


def make_grid_scalar2d_content(
    *,
    data: Optional[Iterable[float]] = None,
    lats: Optional[Sequence[float]] = None,
    lons: Optional[Sequence[float]] = None,
    lat_count: int = 2,
    lon_count: int = 3,
    start_lat: float = 30.0,
    start_lon: float = 110.0,
    end_lat: float = 31.0,
    end_lon: float = 112.0,
    lat_step: float = 1.0,
    lon_step: float = 1.0,
    units: str = SYNTHETIC_UNITS,
    element_name: str = SYNTHETIC_ELEMENT_NAME,
    error_code: int = 0,
    error_message: str = "",
) -> bytes:
    """Serialize a synthetic ``RetGridScalar2D`` response."""

    if data is None:
        data = np.asarray(SYNTHETIC_GRID_VALUES).reshape(-1)
    message = pb.RetGridScalar2D(
        startLat=start_lat,
        startLon=start_lon,
        endLat=end_lat,
        endLon=end_lon,
        latCount=lat_count,
        lonCount=lon_count,
        latStep=lat_step,
        lonStep=lon_step,
        units=units,
        userEleName=element_name,
    )
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=lat_count,
            col_count=lon_count,
        )
    )
    if lats is not None:
        message.lats.extend(lats)
    if lons is not None:
        message.lons.extend(lons)
    message.datas.extend(float(value) for value in data)
    return message.SerializeToString()


def make_grid_scalar2d_response(**kwargs) -> GridScalar2D:
    """Build a :class:`GridScalar2D` from a synthetic serialized response."""

    return GridScalar2D.create_from_protobuf(make_grid_scalar2d_content(**kwargs))


def make_grid_vector2d_content(
    *,
    u_data: Optional[Iterable[float]] = None,
    v_data: Optional[Iterable[float]] = None,
    lats: Optional[Sequence[float]] = None,
    lons: Optional[Sequence[float]] = None,
    lat_count: int = 2,
    lon_count: int = 3,
    start_lat: float = 30.0,
    start_lon: float = 110.0,
    end_lat: float = 31.0,
    end_lon: float = 112.0,
    lat_step: float = 1.0,
    lon_step: float = 1.0,
    u_element_name: str = "synthetic_u_wind",
    v_element_name: str = "synthetic_v_wind",
    error_code: int = 0,
    error_message: str = "",
) -> bytes:
    """Serialize a synthetic ``RetGridVector2D`` response."""

    u_data = SYNTHETIC_U_VALUES if u_data is None else u_data
    v_data = SYNTHETIC_V_VALUES if v_data is None else v_data
    message = pb.RetGridVector2D(
        startLat=start_lat,
        startLon=start_lon,
        endLat=end_lat,
        endLon=end_lon,
        latCount=lat_count,
        lonCount=lon_count,
        latStep=lat_step,
        lonStep=lon_step,
        u_EleName=u_element_name,
        v_EleName=v_element_name,
    )
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=lat_count,
            col_count=lon_count,
        )
    )
    if lats is not None:
        message.lats.extend(lats)
    if lons is not None:
        message.lons.extend(lons)
    message.u_datas.extend(float(value) for value in u_data)
    message.v_datas.extend(float(value) for value in v_data)
    return message.SerializeToString()


def make_grid_vector2d_response(**kwargs) -> GridVector2D:
    """Build a :class:`GridVector2D` from a synthetic serialized response."""

    return GridVector2D.create_from_protobuf(make_grid_vector2d_content(**kwargs))


def make_files_info_content(
    *,
    file_infos: Optional[Sequence[dict]] = None,
    error_code: int = 0,
    error_message: str = "",
) -> bytes:
    """Serialize a synthetic ``RetFilesInfo`` response."""

    file_infos = file_infos if file_infos is not None else [
        {
            "file_name": "synthetic.bin",
            "save_path": "/synthetic/output",
            "suffix": ".bin",
            "size": str(len(SYNTHETIC_FILE_BYTES)),
            "file_url": "https://synthetic.invalid/data.bin",
            "image_base64": "",
            "attributes": ["synthetic", "offline"],
        }
    ]
    message = pb.RetFilesInfo()
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=len(file_infos),
            col_count=1,
        )
    )
    for info in file_infos:
        message.fileInfos.add(
            fileName=info.get("file_name", ""),
            savePath=info.get("save_path", ""),
            suffix=info.get("suffix", ""),
            size=info.get("size", ""),
            fileUrl=info.get("file_url", ""),
            imgBase64=info.get("image_base64", ""),
            attributes=info.get("attributes", []),
        )
    return message.SerializeToString()


def make_files_info_response(**kwargs) -> FilesInfo:
    """Build a :class:`FilesInfo` from a synthetic serialized response."""

    return FilesInfo.create_from_protobuf(make_files_info_content(**kwargs))


def make_data_block_content(
    *,
    data_name: str = "synthetic_block",
    data: bytes = b"synthetic payload",
    error_code: int = 0,
    error_message: str = "",
) -> bytes:
    """Serialize a synthetic ``RetDataBlock`` response."""

    message = pb.RetDataBlock(
        dataName=data_name,
        byteArray=data,
    )
    message.request.CopyFrom(
        make_request_info(
            error_code=error_code,
            error_message=error_message,
            row_count=1,
            col_count=1,
        )
    )
    return message.SerializeToString()


def make_data_block_response(**kwargs) -> DataBlock:
    """Build a :class:`DataBlock` from a synthetic serialized response."""

    return DataBlock.create_from_protobuf(make_data_block_content(**kwargs))
