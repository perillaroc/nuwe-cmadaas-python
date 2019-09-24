# coding: utf-8
import json
import logging
from typing import Callable, Any

import requests

from nuwe_cimiss.data import (
    ResponseData
)

logger = logging.getLogger()


class Connection(object):
    getwayFlag = b'"flag":"slb"'
    otherError = -10001

    def __init__(
            self,
            client
    ):
        self._client = client

    def make_request(
            self,
            fetch_url: str,
            success_handler: Callable[[bytes], Any],
            failure_handler: Callable[[bytes], Any],
            exception_handler: Callable[[Exception], Any],
    ):
        try:
            response = requests.get(
                fetch_url,
                timeout=(self._client.connect_timeout, self._client.read_timeout),
                stream=True,
            )
            response_content = response.content

        except requests.exceptions.RequestException as e:  # http error
            return exception_handler(e)

        if self._check_getway_flag(response_content):
            return failure_handler(response_content)

        return success_handler(response_content)

    @classmethod
    def generate_pack_failure_handler(
            cls,
            response_data: ResponseData,
    ):
        """
        出错返回消息示例：
            {"returnCode":-1004,"flag":"slb","returnMessage":"Password Error"}
        """

        def failure_handler(response_content: bytes):
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
    ):
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
    ):
        def handle_success(response_content: bytes) -> ResponseData:
            response_data.load_from_protobuf_content(response_content)
            return response_data

        return handle_success

    @classmethod
    def _check_getway_flag(cls, response_data: bytes) -> bool:
        return Connection.getwayFlag in response_data
