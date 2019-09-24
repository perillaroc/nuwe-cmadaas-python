# coding: utf-8
from typing import List

import numpy as np

from nuwe_cimiss import apiinterface_pb2 as pb


class RequestInfo(object):
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


class ResponseData(object):
    def __init__(
            self,
            request: RequestInfo = None
    ):
        self.request = request

    def load_from_protobuf_content(self, content: bytes):
        pass


class Array2D(ResponseData):
    def __init__(
            self,
            data: np.array = None,
            request: RequestInfo = None,
            element_names: List[str] = None,
            row_count: int = 0,
            col_count: int = 0,
    ):
        super().__init__(request=request)
        self.data = data
        self.element_names = element_names
        self.row_count = row_count
        self.col_count = col_count

    def load_from_protobuf_content(self, content: bytes):
        pb_ret_array_2d = pb.RetArray2D()
        pb_ret_array_2d.ParseFromString(content)
        self.load_from_protobuf_object(pb_ret_array_2d)

    def load_from_protobuf_object(self, ret_array_2d: pb.RetArray2D):
        self.request = RequestInfo.create_from_protobuf(ret_array_2d.request)
        self.element_names = ret_array_2d.elementNames
        if self.request.error_code != 0:
            return

        self.row_count = ret_array_2d.request.rowCount
        # self.col_count = ret_array_2d.request.colCount
        total_count = len(ret_array_2d.data)
        self.col_count = int(total_count/self.row_count)
        assert(self.col_count == ret_array_2d.request.colCount)

        self.data = np.array(ret_array_2d.data).reshape([self.row_count, self.col_count])

    @classmethod
    def create_from_protobuf(cls, content: bytes):
        array_2d = Array2D()
        array_2d.load_from_protobuf_content(content)
        return array_2d

