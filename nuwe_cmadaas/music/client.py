import configparser
import json
import pathlib
import warnings
import hashlib
import time
import uuid
from copy import deepcopy
from typing import Callable, Any, Dict

from .connection import Connection
from .data import (
    Array2D,
    DataBlock,
    GridArray2D,
    FilesInfo,
    GridScalar2D,
    GridVector2D,
)
from nuwe_cmadaas._log import logger


class CMADaaSClient(object):
    clientLanguage = "Python"
    clientVersion = "V2.0.0"

    def __init__(
            self,
            server_ip: str = None,
            server_port: int = None,
            server_id: str = None,
            connection_timeout: int = None,
            read_timeout: int = None,
            user: str = None,
            password: str = None,
            config: Dict = None,
            config_file: pathlib.Path or str = None,
    ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_id = server_id
        self.connect_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.config_file = config_file
        self.user = user
        self.password = password
        self._connection = None
        self.config = config

        # 数据读取URL
        #   http://ip:port/music-ws/api?serviceNodeId=serverId&
        self.basic_url = (
            "http://{server_ip}:{server_port}/music-ws/api?serviceNodeId={server_id}&"
        )

        if self.config_file is not None:
            self._load_config_from_file()
        if self.config is not None:
            self._load_config()

        self.create_connect(self.user, self.password)

    def create_connect(self, user: str, password: str):
        self.user = user
        self.password = password
        self._connection = Connection(client=self)

    def callAPI_to_array2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> Array2D:
        array_2d = Array2D()

        method = self.callAPI_to_array2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(array_2d),
            failure_handler=Connection.generate_pack_failure_handler(array_2d),
            exception_handler=Connection.generate_exception_handler(array_2d),
        )

    def callAPI_to_gridArray2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> GridArray2D:
        data = GridArray2D()

        method = self.callAPI_to_gridArray2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_fileList(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ):
        data = FilesInfo()

        method = self.callAPI_to_fileList.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_serializedStr(
            self,
            interface_id: str,
            params: Dict,
            data_format: str,
            server_id: str = None
    ):
        if "dataFormat" not in params:
            params["dataFormat"] = data_format

        method = self.callAPI_to_serializedStr.__name__

        def handle_success(content: bytes) -> str:
            return content.decode("utf8")

        def handle_failure(content: bytes) -> str:
            getway_info = json.loads(content)
            if getway_info is None:
                return "parse getway return string error:" + content.decode("utf8")
            else:
                return "getway error: returnCode={return_code} returnMessage={return_message}".format(
                    return_code=getway_info["returnCode"],
                    return_message=getway_info["returnMessage"],
                )

        def handle_exception(exception: Exception):
            logger.warning("Error retrieving data: " + str(exception))
            return "Error retrieving data"

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=handle_success,
            failure_handler=handle_failure,
            exception_handler=handle_exception,
        )

    def callAPI_to_saveAsFile(
        self,
        interface_id: str,
        params: Dict,
        data_format: str,
        file_name: str,
        server_id: str = None,
    ):
        data = FilesInfo()

        if "dataFormat" not in params:
            params["dataFormat"] = data_format

        method = self.callAPI_to_saveAsFile.__name__

        if file_name is None:
            data.request.errorCode = Connection.otherError
            data.request.errorMessage = (
                "error:savePath can't null, the format is dir/file.formart. "
                "For example /data/saveas.xml)")
            return data

        params["savepath"] = file_name

        def handle_success(content: bytes):
            loaded_data = Connection.generate_pack_success_handler(data)(content)
            if loaded_data.request.error_code != 0:
                return loaded_data

            result = self._connection.download_file(
                loaded_data.files_info[0].file_url, file_name
            )
            if result[0] != 0:
                loaded_data.request.errorCode = result[0]
                loaded_data.request.errorMessage = result[1]
            return loaded_data

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=handle_success,
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_downFile(
        self,
        interface_id: str,
        params: Dict,
        file_dir: str,
        server_id: str = None,
    ):
        file_dir_path = pathlib.Path(file_dir)

        data = FilesInfo()

        method = self.callAPI_to_fileList.__name__

        def success_handler(content: bytes):
            files_info = Connection.generate_pack_success_handler(data)(content)
            if files_info.request.error_code != 0:
                return files_info

            for file_info in files_info.files_info:
                result = self._connection.download_file(
                    file_info.file_url, file_dir_path.joinpath(file_info.file_name)
                )
                if result[0] != 0:
                    files_info.request.errorCode = result[0]
                    files_info.request.errorMessage = result[1]
                    return files_info

            return files_info

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=success_handler,
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_dataBlock(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ) -> DataBlock:
        warnings.warn("callAPI_to_dataBlock is not tested")
        data_block = DataBlock()

        method = self.callAPI_to_dataBlock.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data_block),
            failure_handler=Connection.generate_pack_failure_handler(data_block),
            exception_handler=Connection.generate_exception_handler(data_block),
        )

    def callAPI_to_gridScalar2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ):
        warnings.warn("callAPI_to_gridScalar2D is not tested")
        data = GridScalar2D()

        method = self.callAPI_to_gridScalar2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def callAPI_to_gridVector2D(
            self,
            interface_id: str,
            params: Dict,
            server_id: str = None
    ):
        warnings.warn("callAPI_to_gridVector2D is not tested")
        data = GridVector2D()

        method = self.callAPI_to_gridVector2D.__name__

        return self._do_request(
            interface_id,
            method,
            params,
            server_id,
            success_handler=Connection.generate_pack_success_handler(data),
            failure_handler=Connection.generate_pack_failure_handler(data),
            exception_handler=Connection.generate_exception_handler(data),
        )

    def _load_config_from_file(self) -> None:
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

    def _load_config(self) -> None:
        auth_config = self.config["auth"]
        server_config = self.config["server"]

        if self.user is None:
            self.user = auth_config["user"]
        if self.password is None:
            self.password = auth_config["password"]

        if self.server_ip is None:
            self.server_ip = server_config["music_server"]

        if self.server_port is None:
            self.server_port = server_config["music_port"]

        if self.server_id is None:
            self.server_id = server_config["music_ServiceId"]

        if self.connect_timeout is None:
            self.connect_timeout = server_config["music_connTimeout"]

        if self.read_timeout is None:
            self.read_timeout = server_config["music_readTimeout"]

    def _get_fetch_url(
            self,
            interface_id: str,
            method: str,
            params: Dict,
            server_id: str = None,
    ) -> str:
        if server_id is None:
            server_id = self.server_id

        basic_url = self.basic_url.format(
            server_ip=self.server_ip, server_port=self.server_port, server_id=server_id
        )

        fetch_url = (
            f"{basic_url}method={method}&userId={self.user}&interfaceId={interface_id}"
            f"&language={CMADaaSClient.clientLanguage}&clientversion={CMADaaSClient.clientVersion}"
        )

        timestamp = str((round(time.time() * 1000)))
        nonce = str(uuid.uuid1())
        fetch_url += '&timestamp=' + timestamp
        fetch_url += '&nonce=' + nonce

        sign_params = deepcopy(params)
        sign_params['serviceNodeId'] = server_id
        sign_params['method'] = method
        sign_params['userId'] = self.user
        sign_params['interfaceId'] = interface_id
        sign_params['language'] = CMADaaSClient.clientLanguage
        sign_params['clientversion'] = CMADaaSClient.clientVersion
        sign_params['timestamp'] = timestamp
        sign_params['nonce'] = nonce
        sign_params['pwd'] = self.password
        sign = self._get_sign(sign_params)

        if sign == "":
            print("generate sign is None")

        fetch_url += '&sign=' + sign

        for key, value in params.items():
            fetch_url += f"&{key}={value}"

        return fetch_url

    def _do_request(
            self,
            interface_id: str,
            method: str,
            params: Dict,
            server_id: str,
            success_handler: Callable[[bytes], Any],
            failure_handler: Callable[[bytes], Any],
            exception_handler: Callable[[Exception], Any],
    ):
        fetch_url = self._get_fetch_url(
            interface_id, method, params, server_id
        )
        logger.info(f"fetch url: {fetch_url}")

        result = self._connection.make_request(
            fetch_url,
            success_handler,
            failure_handler,
            exception_handler
        )
        return result

    def _get_sign(self, sign_params: Dict) -> str:
        param_string = ""
        if "params" in sign_params:
            paramsVal = sign_params.pop("params")
            keyValList = paramsVal.split("&")
            for keyVal in keyValList:
                sign_params[keyVal.split("=")[0]] = keyVal.split("=")[1]

        keys = sorted(sign_params.keys())
        for key in keys:
            param_string = param_string + key + "=" + sign_params.get(key) + "&"
        if (param_string):
            param_string = param_string[:-1]

        sign = hashlib.md5(param_string.encode(encoding='UTF-8')).hexdigest().upper()
        return sign
