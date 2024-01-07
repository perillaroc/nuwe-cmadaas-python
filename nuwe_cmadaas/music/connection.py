import json
import pathlib
from typing import Callable, Any, Union, Tuple, Optional

import requests

from nuwe_cmadaas._log import logger

from .data import (
    ResponseData
)


class Connection:
    """
    连接类

    Attributes
    ----------
    connect_timeout : float
        连接超时，单位秒
    read_timeout : float
        读取超时，单位秒
    """
    getwayFlag = b'"flag":"slb"'
    otherError = -10001

    def __init__(
            self,
            connect_timeout: float,
            read_timeout: float,
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def make_request(
            self,
            fetch_url: str,
            success_handler: Callable[[bytes], ResponseData],
            failure_handler: Callable[[bytes], ResponseData],
            exception_handler: Callable[[Exception], Any],
    ) -> ResponseData:
        """
        从URL获取响应并处理结果。

        Parameters
        ----------
        fetch_url
            由``CMADaaSClient``生成的URL
        success_handler
            成功回调函数
        failure_handler
            失败回调函数
        exception_handler
            异常回调函数

        Returns
        -------
        ResponseData
        """
        try:
            response = requests.get(
                fetch_url,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            response_content = response.content

        except requests.exceptions.RequestException as e:  # http error
            return exception_handler(e)

        if self._check_getway_flag(response_content):
            return failure_handler(response_content)

        return success_handler(response_content)

    def download_file(
        self, file_url: str, save_file: Union[str, pathlib.Path]
    ) -> Tuple[int, Optional[str]]:
        try:
            response = requests.get(file_url, stream=True)
            response_content = response.content
            if self._check_getway_flag(response_content):
                getway_info = json.loads(response_content)
                if getway_info is None:
                    return Connection.otherError, "parse getway return string error!"
                else:
                    return getway_info["returnCode"], getway_info["returnMessage"]

            with open(save_file, "wb") as f:
                f.write(response_content)

        except requests.exceptions.RequestException as e:  # http error
            return Connection.otherError, "request error"
        except IOError:
            return Connection.otherError, "create file error"

        return 0, None

    @classmethod
    def generate_pack_failure_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[bytes], ResponseData]:
        """
        出错返回消息示例：
            {"returnCode":-1004,"flag":"slb","returnMessage":"Password Error"}
        """

        def failure_handler(response_content: bytes) -> ResponseData:
            getway_info = json.loads(response_content)
            if getway_info is None:
                response_data.request.errorCode = Connection.otherError
                response_data.request.errorMessage = (
                        "parse getway return string error:" + response_content.decode('utf-8')
                )
            else:
                response_data.request.errorCode = getway_info["returnCode"]
                response_data.request.errorMessage = getway_info["returnMessage"]
            return response_data

        return failure_handler

    @classmethod
    def generate_exception_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[Exception], ResponseData]:
        def handle_exception(e: Exception) -> ResponseData:
            logger.warning(f"Error retrieving data: {e}")
            response_data.request.errorCode = Connection.otherError
            response_data.request.errorMessage = "Error retrieving data"
            return response_data

        return handle_exception

    @classmethod
    def generate_pack_success_handler(
            cls,
            response_data: ResponseData,
    ) -> Callable[[bytes], ResponseData]:
        """
        生成处理返回结果的回调函数。
        该函数将反序列化protobuf字节流并填充到响应数据对象中。

        Parameters
        ----------
        response_data
            响应数据对象

        Returns
        -------
        Callable[[bytes], ResponseData]
        """
        def handle_success(response_content: bytes) -> ResponseData:
            response_data.load_from_protobuf_content(response_content)
            return response_data

        return handle_success

    @classmethod
    def _check_getway_flag(cls, response_data: bytes) -> bool:
        return Connection.getwayFlag in response_data
