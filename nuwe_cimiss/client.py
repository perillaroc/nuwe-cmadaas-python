# coding: utf-8
import configparser
import json
import pathlib
from typing import Callable, Any
import logging

import requests

from nuwe_cimiss.data import (
    ResponseData,
    Array2D
)

logger = logging.getLogger()


class CimissClient(object):
    clientLanguage = "Python"
    clientVersion = "V2.0.0"
    getwayFlag = b'"flag":"slb"'

    otherError = -10001

    def __init__(
            self,
            server_ip: str = None,
            server_port: int = None,
            server_id: str = None,
            connection_timeout: int = None,
            read_timeout: int = None,
            config_file: pathlib.Path or str = None,
            user: str = None,
            password: str = None,
    ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_id = server_id
        self.connect_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.config_file = config_file
        self.user = user
        self.password = password

        # 数据读取URL
        #   http://ip:port/music-ws/api?serviceNodeId=serverId&
        self.basic_url = (
            "http://{server_ip}:{server_port}/music-ws/api?serviceNodeId={server_id}&"
        )

        if self.config_file is not None:
            self._load_config()

    def connect(self, user: str, password: str):
        self.user = user
        self.password = password

    def callAPI_to_array2D(
            self,
            interface_id: str,
            params: dict,
            server_id: str = None
    ) -> Array2D:
        array_2d = Array2D()
        method = self.callAPI_to_array2D.__name__

        fetch_url = self._get_fetch_url(
            interface_id, method, params, server_id
        )
        logger.info(f"fetch url: {fetch_url}")

        response_content = self._do_request(fetch_url, array_2d, self._pack_response_error)
        if response_content is None:
            return array_2d

        array_2d.load_from_protobuf_content(response_content)

        return array_2d

    def _load_config(self) -> None:
        if self.config_file is not None:
            self.config_file = pathlib.Path(self.config_file)
            if not self.config_file.exists():
                raise RuntimeError(f"config file is not exist: {self.config_file.absolute()}")
        else:
            self.config_file = pathlib.Path("client.config")
            if not self.config_file.exists():
                raise RuntimeError(f"default config file is not exist: {self.config_file.absolute()}")

        cf = configparser.ConfigParser()
        cf.read(self.config_file)

        if self.server_ip is None:
            self.server_ip = cf.get("Pb", "music_server")

        if self.server_port is None:
            self.server_port = cf.getint("Pb", "music_port")

        if self.server_id is None:
            self.server_id = cf.get("Pb", "music_ServiceId")

        if self.connect_timeout is None:
            self.connect_timeout = int(cf.get("Pb", "music_connTimeout"))

        if self.read_timeout is None:
            self.read_timeout = int(cf.get("Pb", "music_readTimeout"))

    def _get_fetch_url(
        self,
        interface_id: str,
        method: str,
        params: dict,
        server_id: str = None,
    ) -> str:
        if server_id is None:
            server_id = self.server_id

        basic_url = self.basic_url.format(
            server_ip=self.server_ip, server_port=self.server_port, server_id=server_id
        )

        fetch_url = (
            f"{basic_url}method={method}&userId={self.user}&pwd={self.password}&interfaceId={interface_id}"
            f"&language={CimissClient.clientLanguage}&clientversion={CimissClient.clientVersion}"
        )

        for key, value in params.items():
            fetch_url += f"&{key}={value}"

        return fetch_url

    def _do_request(
            self,
            fetch_url: str,
            response_data: ResponseData,
            handler: Callable[[ResponseData, bytes], Any]
    ) -> Any:
        try:
            response = requests.get(
                fetch_url,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            response_content = response.content

        except requests.exceptions.RequestException as e:  # http error
            logger.warning(f"Error retrieving data: {e}")
            response_data.request.errorCode = CimissClient.otherError
            response_data.request.errorMessage = "Error retrieving data"
            return None

        if self._check_getway_flag(response_content):
            handler(response_data, response_content)
            return None

        return response_content

    @classmethod
    def _check_getway_flag(cls, response_data: bytes) -> bool:
        return CimissClient.getwayFlag in response_data

    @classmethod
    def _pack_response_error(
            cls,
            response_data: ResponseData,
            response_content: bytes,
    ):
        """
        出错返回消息示例：
            {"returnCode":-1004,"flag":"slb","returnMessage":"Password Error"}
        """
        getway_info = json.loads(response_content)
        if getway_info is None:
            response_data.request.errorCode = CimissClient.otherError
            response_data.request.errorMessage = (
                    "parse getway return string error:" + response_content.decode('utf-8')
            )
        else:
            response_data.request.errorCode = getway_info["returnCode"]
            response_data.request.errorMessage = getway_info["returnMessage"]
        return None
