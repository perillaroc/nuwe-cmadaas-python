from typing import List
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xarray as xr

from nuwe_cmadaas.music import apiinterface_pb2 as pb
from .errors import error_from_request


@dataclass
class MusicError:
    code: int
    message: str


def _empty_grid() -> np.ndarray:
    return np.empty((0, 0), dtype=float)


def _grid_axis(
        values,
        start: float,
        end: float,
        step: float,
        count: int,
        axis_name: str,
) -> list[float]:
    if count < 0:
        raise ValueError(f"{axis_name} count must be non-negative; got {count}")
    if values is not None and len(values) > 0:
        axis = list(values)
    elif count > 0 and step == 0:
        axis = list(np.linspace(start, end, count, endpoint=True))
    else:
        axis = [start + i * step for i in range(count)]
    if len(axis) != count:
        raise ValueError(
            f"{axis_name} coordinate length does not match grid dimensions: "
            f"{len(axis)} != {count}"
        )
    return axis


def _validate_grid_values(
        response_name: str,
        lat_count: int,
        lon_count: int,
        lats,
        lons,
        **values,
) -> tuple[list[float], list[float]]:
    if lat_count < 0 or lon_count < 0:
        raise ValueError(
            f"{response_name} dimensions must be non-negative; "
            f"got {lat_count} * {lon_count}"
        )
    if len(lats) != lat_count:
        raise ValueError(
            f"{response_name} latitude coordinate length does not match "
            f"grid dimensions: {len(lats)} != {lat_count}"
        )
    if len(lons) != lon_count:
        raise ValueError(
            f"{response_name} longitude coordinate length does not match "
            f"grid dimensions: {len(lons)} != {lon_count}"
        )
    expected = lat_count * lon_count
    for name, data in values.items():
        actual = np.asarray(data).size
        if actual != expected:
            value_name = "data" if name == "data" else f"{name} data"
            raise ValueError(
                f"{response_name} {value_name} length does not match grid "
                f"dimensions: {actual} != {lat_count} * {lon_count}"
            )
    return list(lats), list(lons)


def _grid_coordinates(
        start_lat: float,
        end_lat: float,
        lat_step: float,
        lat_count: int,
        lats,
        start_lon: float,
        end_lon: float,
        lon_step: float,
        lon_count: int,
        lons,
) -> dict:
    lats = _grid_axis(
        lats, start_lat, end_lat, lat_step, lat_count, "latitude"
    )
    lons = _grid_axis(
        lons, start_lon, end_lon, lon_step, lon_count, "longitude"
    )
    return {
        "latitude": xr.Variable(
            "latitude",
            lats,
            attrs={
                "units": "degrees_north",
                "standard_name": "latitude",
                "long_name": "latitude",
            },
        ),
        "longitude": xr.Variable(
            "longitude",
            lons,
            attrs={
                "units": "degrees_east",
                "standard_name": "longitude",
                "long_name": "longitude",
            },
        ),
    }


class RequestInfo:
    def __init__(
            self,
            error_code: int = 0,
            error_message: str = "",
            request_elements: str = "",
            request_params: str = "",
            request_time: str = "",
            response_time: str = "",
            row_count: int = 0,
            take_time: int = 0,
            col_count: int = 0,
            pb_request_info: pb.RequestInfo = None,
            cause: BaseException = None,
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.request_elements = request_elements
        self.request_params = request_params
        self.request_time = request_time
        self.response_time = response_time
        self.row_count = row_count
        self.take_time = take_time
        self.col_count = col_count
        self.cause = cause

        if pb_request_info is not None:
            self.load_protobuf(pb_request_info)

    def load_protobuf(self, request_info: pb.RequestInfo):
        self.error_code = request_info.errorCode
        self.error_message = request_info.errorMessage
        self.request_elements = request_info.requestElems
        self.request_params = request_info.requestParams
        self.request_time = request_info.requestTime
        self.response_time = request_info.responseTime
        self.row_count = request_info.rowCount
        self.take_time = request_info.takeTime
        self.col_count = request_info.colCount

    @classmethod
    def create_from_protobuf(cls, request_info: pb.RequestInfo):
        r = RequestInfo()
        r.load_protobuf(request_info)
        return r


class ResponseData:
    def __init__(
            self,
            request: RequestInfo = None
    ):
        if request is None:
            request = RequestInfo()
        self.request = request
        self.metadata = {}

    @property
    def ok(self) -> bool:
        """Whether the MUSIC response contains no request error."""
        return self.request.error_code == 0

    def raise_for_error(self, *, interface_id=None, params=None):
        """Raise a structured exception when the response contains an error.

        The method is intentionally a no-op for successful responses so it can
        be used by callers immediately after every compatible client call.
        """
        if self.ok:
            return self
        error = error_from_request(
            self.request,
            interface_id=interface_id,
            params=params,
            cause=getattr(self.request, "cause", None),
        )
        if error.cause is not None:
            raise error from error.cause
        raise error

    def _ensure_convertible(self):
        if not self.ok:
            self.raise_for_error()

    def _output_metadata(self) -> dict:
        metadata = dict(self.metadata)
        request_metadata = {
            "request_time": self.request.request_time,
            "response_time": self.request.response_time,
        }
        for key, value in request_metadata.items():
            if value and key not in metadata:
                metadata[key] = value
        return metadata

    def load_from_protobuf_content(self, content: bytes):
        raise NotImplementedError()

    @classmethod
    def create_from_protobuf(cls, content: bytes) -> "ResponseData":
        data = cls()
        data.load_from_protobuf_content(content)
        return data

    def to_pandas(self) -> pd.DataFrame:
        raise NotImplementedError()

    def to_xarray(self) -> xr.DataArray:
        raise NotImplementedError()


class Array2D(ResponseData):
    protobuf_object_type = pb.RetArray2D

    def __init__(
            self,
            data: np.ndarray = None,
            request: RequestInfo = None,
            element_names: List[str] = None,
            row_count: int = 0,
            col_count: int = 0,
    ):
        super().__init__(request=request)
        self.data = np.empty((0, 0), dtype=object) if data is None else data
        self.element_names = [] if element_names is None else list(element_names)
        self.row_count = row_count
        self.col_count = col_count

    def to_pandas(self) -> pd.DataFrame:
        self._ensure_convertible()
        data = np.asarray(self.data)
        if data.ndim != 2 or data.shape[1] != len(self.element_names):
            raise ValueError(
                "Array2D data shape does not match element names: "
                f"{data.shape} and {len(self.element_names)}"
            )
        df = pd.DataFrame(data, columns=self.element_names)
        df.attrs.update(self._output_metadata())
        return df

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_array_2d: pb.RetArray2D):
        self.request = RequestInfo.create_from_protobuf(ret_array_2d.request)
        self.element_names = [i for i in ret_array_2d.elementNames]
        if self.request.error_code != 0:
            self.data = np.empty((0, 0), dtype=object)
            self.row_count = 0
            self.col_count = 0
            return

        self.row_count = ret_array_2d.request.rowCount
        self.col_count = ret_array_2d.request.colCount
        if self.row_count < 0 or self.col_count < 0:
            raise ValueError(
                "Array2D dimensions must be non-negative: "
                f"{self.row_count} * {self.col_count}"
            )
        if len(self.element_names) != self.col_count:
            raise ValueError(
                "Array2D element name count does not match columns: "
                f"{len(self.element_names)} != {self.col_count}"
            )
        total_count = len(ret_array_2d.data)
        expected_count = self.row_count * self.col_count
        if total_count != expected_count:
            raise ValueError(
                "Array2D data length does not match request dimensions: "
                f"{total_count} != {self.row_count} * {self.col_count}"
            )

        self.data = np.array(ret_array_2d.data).reshape([self.row_count, self.col_count])


class DataBlock(ResponseData):
    protobuf_object_type = pb.RetDataBlock

    def __init__(
            self,
            data_name: str = None,
            data: bytes = None,
            request: RequestInfo = None,
    ):
        super().__init__(request=request)
        self.data_name = "" if data_name is None else data_name
        self.data = b"" if data is None else data

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_data_block: pb.RetDataBlock):
        self.request = RequestInfo.create_from_protobuf(ret_data_block.request)
        self.data_name = ret_data_block.dataName
        self.data = ret_data_block.byteArray


class GridArray2D(ResponseData):
    protobuf_object_type = pb.RetGridArray2D

    def __init__(
            self,
            data: List[float] = None,
            request: RequestInfo = None,
            start_lat: float = 0,
            start_lon: float = 0,
            end_lat: float = 0,
            end_lon: float = 0,
            lat_count: int = 0,
            lon_count: int = 0,
            lon_step: float = 0,
            lat_step: float = 0,
            lats: List[float] = None,
            lons: List[float] = None,
            units: str = "",
            user_element_name: str = "",
    ):
        super().__init__(request=request)
        self.data = _empty_grid() if data is None else data
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.end_lat = end_lat
        self.end_lon = end_lon
        self.lat_count = lat_count
        self.lon_count = lon_count
        self.lon_step = lon_step
        self.lat_step = lat_step
        self.lats = [] if lats is None else list(lats)
        self.lons = [] if lons is None else list(lons)
        self.units = units
        self.user_element_name = user_element_name

    def to_xarray(self) -> xr.DataArray:
        self._ensure_convertible()
        data = np.asarray(self.data)
        if data.ndim != 2 or data.shape != (self.lat_count, self.lon_count):
            raise ValueError(
                "GridArray2D data shape does not match grid dimensions: "
                f"{data.shape} != ({self.lat_count}, {self.lon_count})"
            )
        coords = _grid_coordinates(
            self.start_lat, self.end_lat, self.lat_step, self.lat_count,
            self.lats, self.start_lon, self.end_lon, self.lon_step,
            self.lon_count, self.lons,
        )

        dims = ("latitude", "longitude")

        field = xr.DataArray(
            data,
            dims=dims,
            coords=coords,
            attrs={
                "units": self.units,
                **self._output_metadata(),
            },
            name=self.user_element_name,
        )

        return field

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_grid_array_2d: pb.RetGridArray2D):
        self.request = RequestInfo.create_from_protobuf(ret_grid_array_2d.request)

        if self.request.error_code != 0:
            self.data = _empty_grid()
            self.lats = []
            self.lons = []
            self.lat_count = 0
            self.lon_count = 0
            return

        self.start_lat = ret_grid_array_2d.startLat
        self.start_lon = ret_grid_array_2d.startLon
        self.end_lat = ret_grid_array_2d.endLat
        self.end_lon = ret_grid_array_2d.endLon
        self.lat_count = ret_grid_array_2d.latCount
        self.lon_count = ret_grid_array_2d.lonCount
        self.lon_step = ret_grid_array_2d.lonStep
        self.lat_step = ret_grid_array_2d.latStep

        self.lats = _grid_axis(
            ret_grid_array_2d.lats,
            self.start_lat, self.end_lat, self.lat_step,
            self.lat_count, "latitude",
        )
        self.lons = _grid_axis(
            ret_grid_array_2d.lons,
            self.start_lon, self.end_lon, self.lon_step,
            self.lon_count, "longitude",
        )

        self.units = ret_grid_array_2d.units
        self.user_element_name = ret_grid_array_2d.userEleName

        _validate_grid_values(
            "GridArray2D", self.lat_count, self.lon_count,
            self.lats, self.lons, data=ret_grid_array_2d.data,
        )
        self.data = np.array(ret_grid_array_2d.data).reshape(
            [self.lat_count, self.lon_count]
        )


class FileInfo:
    def __init__(
            self,
            file_name: str = "",
            save_path: str = "",
            suffix: str = "",
            size: str = "",
            file_url: str = "",
            image_base64: str = "",
            attributes: List[str] = None,
    ):
        self.file_name = file_name
        self.save_path = save_path
        self.suffix = suffix
        self.size = size
        self.file_url = file_url
        self.image_base64 = image_base64
        self.attributes = [] if attributes is None else list(attributes)

    @classmethod
    def create_from_protobuf(cls, pb_file_info: pb.FileInfo):
        return FileInfo(
            file_name=pb_file_info.fileName,
            save_path=pb_file_info.savePath,
            suffix=pb_file_info.suffix,
            size=pb_file_info.size,
            file_url=pb_file_info.fileUrl,
            image_base64=pb_file_info.imgBase64,
            attributes=pb_file_info.attributes,
        )


class FilesInfo(ResponseData):
    protobuf_object_type = pb.RetFilesInfo

    def __init__(self, files_info: List[FileInfo] = None, request: RequestInfo = None):
        super().__init__(request)
        self.files_info = [] if files_info is None else list(files_info)

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_files_info: pb.RetFilesInfo):
        self.request = RequestInfo.create_from_protobuf(ret_files_info.request)

        if self.request.error_code != 0:
            self.files_info = []
            return

        files_info = ret_files_info.fileInfos
        self.files_info = [FileInfo.create_from_protobuf(info) for info in files_info]


class GridVector2D(ResponseData):
    protobuf_object_type = pb.RetGridVector2D

    def __init__(
            self,
            u_datas: List[float] = None,
            v_datas: List[float] = None,
            request: RequestInfo = None,
            start_lat: float = 0,
            start_lon: float = 0,
            end_lat: float = 0,
            end_lon: float = 0,
            lat_count: int = 0,
            lon_count: int = 0,
            lon_step: float = 0,
            lat_step: float = 0,
            lats: List[float] = None,
            lons: List[float] = None,
            u_element_name: str = "",
            v_element_name: str = "",
    ):
        super().__init__(request)
        self.u_datas = _empty_grid() if u_datas is None else u_datas
        self.v_datas = _empty_grid() if v_datas is None else v_datas
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.end_lat = end_lat
        self.end_lon = end_lon
        self.lat_count = lat_count
        self.lon_count = lon_count
        self.lon_step = lon_step
        self.lat_step = lat_step
        self.lats = [] if lats is None else list(lats)
        self.lons = [] if lons is None else list(lons)
        self.u_element_name = u_element_name
        self.v_element_name = v_element_name

    def to_xarray(self) -> xr.Dataset:
        self._ensure_convertible()
        u_data = np.asarray(self.u_datas)
        v_data = np.asarray(self.v_datas)
        _validate_grid_values(
            "GridVector2D", self.lat_count, self.lon_count,
            self.lats, self.lons, u_datas=u_data, v_datas=v_data,
        )
        shape = (self.lat_count, self.lon_count)
        if u_data.shape != shape or v_data.shape != shape:
            raise ValueError(
                "GridVector2D data shape does not match grid dimensions: "
                f"{u_data.shape}, {v_data.shape} != {shape}"
            )
        return xr.Dataset(
            data_vars={
                self.u_element_name or "u": (("latitude", "longitude"), u_data),
                self.v_element_name or "v": (("latitude", "longitude"), v_data),
            },
            coords=_grid_coordinates(
                self.start_lat, self.end_lat, self.lat_step, self.lat_count,
                self.lats, self.start_lon, self.end_lon, self.lon_step,
                self.lon_count, self.lons,
            ),
            attrs=self._output_metadata(),
        )

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_grid_vector_2d: pb.RetGridVector2D):
        self.request = RequestInfo.create_from_protobuf(ret_grid_vector_2d.request)

        if self.request.error_code != 0:
            self.u_datas = _empty_grid()
            self.v_datas = _empty_grid()
            self.lats = []
            self.lons = []
            self.lat_count = 0
            self.lon_count = 0
            return

        self.start_lat = ret_grid_vector_2d.startLat
        self.start_lon = ret_grid_vector_2d.startLon
        self.end_lat = ret_grid_vector_2d.endLat
        self.end_lon = ret_grid_vector_2d.endLon
        self.lat_count = ret_grid_vector_2d.latCount
        self.lon_count = ret_grid_vector_2d.lonCount
        self.lon_step = ret_grid_vector_2d.lonStep
        self.lat_step = ret_grid_vector_2d.latStep

        self.lats = _grid_axis(
            ret_grid_vector_2d.lats,
            self.start_lat, self.end_lat, self.lat_step,
            self.lat_count, "latitude",
        )
        self.lons = _grid_axis(
            ret_grid_vector_2d.lons,
            self.start_lon, self.end_lon, self.lon_step,
            self.lon_count, "longitude",
        )

        self.u_element_name = ret_grid_vector_2d.u_EleName
        self.v_element_name = ret_grid_vector_2d.v_EleName

        row_count = self.lat_count
        col_count = self.lon_count
        _validate_grid_values(
            "GridVector2D", row_count, col_count, self.lats, self.lons,
            u_datas=ret_grid_vector_2d.u_datas,
            v_datas=ret_grid_vector_2d.v_datas,
        )
        self.u_datas = np.array(ret_grid_vector_2d.u_datas).reshape(
            [row_count, col_count]
        )
        self.v_datas = np.array(ret_grid_vector_2d.v_datas).reshape(
            [row_count, col_count]
        )


class GridScalar2D(ResponseData):
    protobuf_object_type = pb.RetGridScalar2D

    def __init__(
            self,
            data: List[float] = None,
            request: RequestInfo = None,
            start_lat: float = 0,
            start_lon: float = 0,
            end_lat: float = 0,
            end_lon: float = 0,
            lat_count: int = 0,
            lon_count: int = 0,
            lon_step: float = 0,
            lat_step: float = 0,
            lats: List[float] = None,
            lons: List[float] = None,
            units: str = "",
            user_element_name: str = "",
    ):
        super().__init__(request)
        self.data = _empty_grid() if data is None else data
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.end_lat = end_lat
        self.end_lon = end_lon
        self.lat_count = lat_count
        self.lon_count = lon_count
        self.lon_step = lon_step
        self.lat_step = lat_step
        self.lats = [] if lats is None else list(lats)
        self.lons = [] if lons is None else list(lons)
        self.units = units
        self.user_element_name = user_element_name

    def to_xarray(self) -> xr.DataArray:
        self._ensure_convertible()
        data = np.asarray(self.data)
        shape = (self.lat_count, self.lon_count)
        if data.ndim != 2 or data.shape != shape:
            raise ValueError(
                "GridScalar2D data shape does not match grid dimensions: "
                f"{data.shape} != {shape}"
            )
        return xr.DataArray(
            data,
            dims=("latitude", "longitude"),
            coords=_grid_coordinates(
                self.start_lat, self.end_lat, self.lat_step, self.lat_count,
                self.lats, self.start_lon, self.end_lon, self.lon_step,
                self.lon_count, self.lons,
            ),
            attrs={"units": self.units, **self._output_metadata()},
            name=self.user_element_name,
        )

    def load_from_protobuf_content(self, content: bytes):
        protobuf_object = self.protobuf_object_type()
        protobuf_object.ParseFromString(content)
        self.load_from_protobuf_object(protobuf_object)

    def load_from_protobuf_object(self, ret_grid_scalar_2d: pb.RetGridScalar2D):
        self.request = RequestInfo.create_from_protobuf(ret_grid_scalar_2d.request)

        if self.request.error_code != 0:
            self.data = _empty_grid()
            self.lats = []
            self.lons = []
            self.lat_count = 0
            self.lon_count = 0
            return

        self.start_lat = ret_grid_scalar_2d.startLat
        self.start_lon = ret_grid_scalar_2d.startLon
        self.end_lat = ret_grid_scalar_2d.endLat
        self.end_lon = ret_grid_scalar_2d.endLon
        self.lat_count = ret_grid_scalar_2d.latCount
        self.lon_count = ret_grid_scalar_2d.lonCount
        self.lon_step = ret_grid_scalar_2d.lonStep
        self.lat_step = ret_grid_scalar_2d.latStep

        self.lats = _grid_axis(
            ret_grid_scalar_2d.lats,
            self.start_lat, self.end_lat, self.lat_step,
            self.lat_count, "latitude",
        )
        self.lons = _grid_axis(
            ret_grid_scalar_2d.lons,
            self.start_lon, self.end_lon, self.lon_step,
            self.lon_count, "longitude",
        )

        self.units = ret_grid_scalar_2d.units
        self.user_element_name = ret_grid_scalar_2d.userEleName

        row_count = self.lat_count
        col_count = self.lon_count
        _validate_grid_values(
            "GridScalar2D", row_count, col_count, self.lats, self.lons,
            data=ret_grid_scalar_2d.datas,
        )
        self.data = np.array(ret_grid_scalar_2d.datas).reshape(
            [row_count, col_count]
        )
