#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
data query interface class
Created on 2016年3月28日
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr

Modified in 2019/3/6
@author: wufy
"""

import configparser
import json
import os
import socket
from io import BytesIO
import warnings
import pathlib
import logging

import requests

from cma.music import DataFormatUtils
from cma.music import apiinterface_pb2
from cma.music.MusicDataBean import (
    RetArray2D,
    RetGridArray2D,
    RetGridVector2D,
    RetFilesInfo,
    RetDataBlock,
    RetGridScalar2D,
)


logger = logging.getLogger()


class DataQueryClient(object):
    """
    data query interface class
    """

    language = "Python"  # 客户端语言
    clientVersion = "V2.0.0"  # 客户端版本
    getwayFlag = b'"flag":"slb"'  # 网关返回错误标识

    def __init__(
        self,
        server_ip: str = None,
        server_port: int = None,
        service_node_id: str = None,
        connection_timeout: int = None,
        read_timeout: int = None,
        config_file: str = None,
    ):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_id = service_node_id
        self.connect_timeout = connection_timeout
        self.read_timeout = read_timeout

        # 本机IP
        self.client_ip = socket.gethostbyname(socket.gethostname())

        # 数据读取URL(基本路径) http://ip:port/music-ws/api?serviceNodeId=serverId&
        self.basic_url = (
            "http://{server_ip}:{server_port}/music-ws/api?serviceNodeId={server_id}&"
        )

        # return error code
        self.OTHER_ERROR = -10001  # 其他异常

        self._load_config(config_file)

    def callAPI_to_array2D(
        self,
        user_id: str,
        pwd: str,
        interface_id: str,
        params: dict,
        server_id: str = None,
    ):
        """
        站点资料（要素）数据检索
        """
        ret_array_2d = RetArray2D()

        # 所要调用的方法名称
        method = "callAPI_to_array2D"

        # 构建music protobuf服务器地址，将请求参数拼接为url
        fetch_url = self._get_fetch_url(
            user_id, pwd, interface_id, params, server_id, method
        )
        logger.info(f"URL: {fetch_url}")

        response_content = self._do_request(fetch_url, ret_array_2d)
        if response_content is None:
            return ret_array_2d

        # 反序列化为proto的结果
        pb_ret_array_2d = apiinterface_pb2.RetArray2D()
        pb_ret_array_2d.ParseFromString(response_content)
        utils = DataFormatUtils.Utils()
        ret_array_2d = utils.get_array_2d(pb_ret_array_2d)

        return ret_array_2d

    def callAPI_to_dataBlock(
        self,
        user_id: str,
        pwd: str,
        interface_id: str,
        params: dict,
        server_id: str = None,
    ):
        """
            数据块检索
        """
        warnings.warn("callAPI_to_dataBlock is not tested")

        ret_data_block = RetDataBlock()
        # 所要调用的方法名称
        method = "callAPI_to_dataBlock"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        fetch_url = self._get_fetch_url(
            user_id, pwd, interface_id, params, server_id, method
        )
        logger.info(f"URL: {fetch_url}")

        response_content = self._do_request(fetch_url, ret_data_block)
        if response_content is None:
            return response_content

        pb_data_block = apiinterface_pb2.RetDataBlock()
        pb_data_block.ParseFromString(response_content)
        # 格式转换
        utils = DataFormatUtils.Utils()
        ret_data_block = utils.get_data_block(pb_data_block)

        return ret_data_block

    def callAPI_to_gridArray2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     网格数据检索
        """
        retGridArray2D = RetGridArray2D()
        # 所要调用的方法名称
        method = "callAPI_to_gridArray2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self._get_fetch_url(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
            response.setopt(pycurl.TIMEOUT, self.read_timeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retGridArray2D.request.errorCode = self.OTHER_ERROR
            retGridArray2D.request.errorMessage = "Error retrieving data"
            return retGridArray2D

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retGridArray2D.request.errorCode = self.OTHER_ERROR
                retGridArray2D.request.errorMessage = (
                    "parse getway return string error!"
                )
            else:
                retGridArray2D.request.errorCode = getwayInfo["returnCode"]
                retGridArray2D.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbGridArray2D = apiinterface_pb2.RetGridArray2D()
            pbGridArray2D.ParseFromString(RetByteArraydata)
            # 格式转换
            utils = DataFormatUtils.Utils()
            retGridArray2D = utils.get_grid_array_2d(pbGridArray2D)

        return retGridArray2D

    def callAPI_to_fileList(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     文件存储信息列表检索
        """
        retFilesInfo = RetFilesInfo()
        # 所要调用的方法名称
        method = "callAPI_to_fileList"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self._get_fetch_url(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
            response.setopt(pycurl.TIMEOUT, self.read_timeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retFilesInfo.request.errorCode = self.OTHER_ERROR
            retFilesInfo.request.errorMessage = "Error retrieving data"
            return retFilesInfo

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retFilesInfo.request.errorCode = self.OTHER_ERROR
                retFilesInfo.request.errorMessage = "parse getway return string error!"
            else:
                retFilesInfo.request.errorCode = getwayInfo["returnCode"]
                retFilesInfo.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbRetFilesInfo = apiinterface_pb2.RetFilesInfo()
            pbRetFilesInfo.ParseFromString(RetByteArraydata)
            # 格式转换，生成music的结果
            utils = DataFormatUtils.Utils()
            retFilesInfo = utils.get_ret_files_info(pbRetFilesInfo)

        return retFilesInfo

    def callAPI_to_serializedStr(
        self, userId, pwd, interfaceId, params, dataFormat, serverId=None
    ):
        """
        检索数据并序列化结果
        """
        # 所要调用的方法名称
        method = "callAPI_to_serializedStr"

        # 添加数据格式
        if "dataFormat" not in params:
            params["dataFormat"] = dataFormat

        # 构建music protobuf服务器地址，将请求参数拼接为url
        fetch_url = self._get_fetch_url(
            userId, pwd, interfaceId, params, serverId, method
        )
        logger.info(f"URL: {fetch_url}")

        try:
            response = requests.get(
                fetch_url,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            response_content = response.content

        except requests.exceptions.RequestException as e:  # http error
            logger.warning("Error retrieving data")
            return "Error retrieving data"

        if DataQueryClient.getwayFlag in response_content:  # 网关错误
            getway_info = json.loads(response_content)
            if getway_info is None:
                return "parse getway return string error:" + response_content.decode(
                    "utf8"
                )
            else:
                return "getway error: returnCode={return_code} returnMessage={return_message}".format(
                    return_code=getway_info["returnCode"],
                    return_message=getway_info["returnMessage"],
                )

        return response_content.decode("utf8")

    def callAPI_to_saveAsFile(
        self,
        user_id: str,
        pwd: str,
        interface_id: str,
        params: dict,
        data_format: str,
        file_name: str,
        server_id: str = None,
    ):
        """
        把结果存成文件下载到本地（检索结果为要素，服务端保存为文件）
        """
        ret_files_info = RetFilesInfo()

        # 所要调用的方法名称
        method = "callAPI_to_saveAsFile"

        # 添加数据格式
        if "dataFormat" not in params:
            params["dataFormat"] = data_format

        if file_name is None:
            ret_files_info.request.errorCode = self.OTHER_ERROR
            ret_files_info.request.errorMessage = "error:savePath can't null, the format is dir/file.formart. For example /data/saveas.xml)"
            return ret_files_info

        params["savepath"] = file_name

        # 构建music protobuf服务器地址，将请求参数拼接为url
        fetch_url = self._get_fetch_url(
            user_id, pwd, interface_id, params, server_id, method
        )
        logger.info(f"URL: {fetch_url}")

        response_content = self._do_request(fetch_url, ret_files_info)
        if response_content is None:
            return ret_files_info

        pb_ret_files_info = apiinterface_pb2.RetFilesInfo()
        pb_ret_files_info.ParseFromString(response_content)
        utils = DataFormatUtils.Utils()
        ret_files_info = utils.get_ret_files_info(pb_ret_files_info)

        # 将数据保存到本地
        if ret_files_info and ret_files_info.request.errorCode == 0:
            result = self._download_file(
                ret_files_info.file_infos[0].fileUrl, file_name
            )
            if result[0] != 0:
                ret_files_info.request.errorCode = result[0]
                ret_files_info.request.errorMessage = result[1]

        return ret_files_info

    def callAPI_to_downFile(
        self,
        user_id: str,
        pwd: str,
        interface_id: str,
        params: dict,
        file_dir: str,
        server_id: str = None,
    ):
        """
        检索并下载文件
        """
        file_dir_path = pathlib.Path(file_dir)

        ret_files_info = RetFilesInfo()

        # 所要调用的方法名称   打印该函数名称
        method = "callAPI_to_fileList"

        # 构建music protobuf服务器地址，将请求参数拼接为url
        fetch_url = self._get_fetch_url(
            user_id, pwd, interface_id, params, server_id, method
        )
        logger.info(f"URL: {fetch_url}")

        response_content = self._do_request(fetch_url, ret_files_info)
        if response_content is None:
            return ret_files_info

        pb_ret_files_info = apiinterface_pb2.RetFilesInfo()
        pb_ret_files_info.ParseFromString(response_content)
        utils = DataFormatUtils.Utils()
        ret_files_info = utils.get_ret_files_info(pb_ret_files_info)

        if ret_files_info and ret_files_info.request.errorCode == 0:
            for info in ret_files_info.file_infos:
                result = self._download_file(
                    info.fileUrl, file_dir_path.joinpath(info.fileName)
                )
                if result[0] != 0:
                    ret_files_info.request.errorCode = result[0]
                    ret_files_info.request.errorMessage = result[1]
                    return ret_files_info

        return ret_files_info

    def callAPI_to_downFile_ByUrl(self, fileURL, save_as):
        """
                    根据url下载文件
        """
        result = self._download_file(fileURL, save_as)
        if result[0] == 0:
            print("download file success!")
        else:
            print("download file failed:" + fileURL)

        return result

    def callAPI_to_gridScalar2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     网格矢量数据
        """
        retGridScalar2D = RetGridScalar2D()
        # 所要调用的方法名称
        method = "callAPI_to_gridScalar2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self._get_fetch_url(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
            response.setopt(pycurl.TIMEOUT, self.read_timeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retGridScalar2D.request.errorCode = self.OTHER_ERROR
            retGridScalar2D.request.errorMessage = "Error retrieving data"
            return retGridScalar2D

        buf.flush()
        RetByteArraydata = buf.getvalue()
        buf.close()
        print(len(RetByteArraydata))
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retGridScalar2D.request.errorCode = self.OTHER_ERROR
                retGridScalar2D.request.errorMessage = (
                    "parse getway return string error!"
                )
            else:
                retGridScalar2D.request.errorCode = getwayInfo["returnCode"]
                retGridScalar2D.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbGridScalar2D = apiinterface_pb2.RetGridScalar2D()
            pbGridScalar2D.ParseFromString(RetByteArraydata)
            # 格式转换，生成music的结果
            print(pbGridScalar2D.request)
            utils = DataFormatUtils.Utils()
            retGridScalar2D = utils.get_grid_scalar_2d(pbGridScalar2D)

        return retGridScalar2D

    def callAPI_to_gridVector2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     网格矢量数据
        """
        retGridVector2D = RetGridVector2D()
        # 所要调用的方法名称
        method = "callAPI_to_gridVector2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self._get_fetch_url(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            # buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connect_timeout)
            response.setopt(pycurl.TIMEOUT, self.read_timeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retGridVector2D.request.errorCode = self.OTHER_ERROR
            retGridVector2D.request.errorMessage = "Error retrieving data"
            return retGridVector2D

        RetByteArraydata = buf.getvalue()
        # print len(RetByteArraydata)
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retGridVector2D.request.errorCode = self.OTHER_ERROR
                retGridVector2D.request.errorMessage = (
                    "parse getway return string error!"
                )
            else:
                retGridVector2D.request.errorCode = getwayInfo["returnCode"]
                retGridVector2D.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbGridVector2D = apiinterface_pb2.RetGridVector2D()
            pbGridVector2D.ParseFromString(RetByteArraydata)
            # print pbGridVector2D.request
            utils = DataFormatUtils.Utils()
            retGridVector2D = utils.get_grid_vector_2d(pbGridVector2D)

        return retGridVector2D

    def _load_config(self, config_file: str) -> None:
        if config_file is not None:
            if not os.path.exists(config_file):
                raise RuntimeError("config file is not exist.")
            else:
                config = config_file
        else:
            default_config = "client.config"
            if pathlib.Path(default_config).exists():
                config = default_config
            else:
                raise RuntimeError("default config file is not exist.")

        cf = configparser.ConfigParser()
        cf.read(config)

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
        user_id: str,
        pwd: str,
        interface_id: str,
        params: dict,
        server_id: str,
        method: str,
    ) -> str:
        """
        将请求参数拼接为url
        """
        if server_id is None:
            server_id = self.server_id

        basic_url = self.basic_url.format(
            server_ip=self.server_ip, server_port=self.server_port, server_id=server_id
        )

        fetch_url = (
            f"{basic_url}method={method}&userId={user_id}&pwd={pwd}&interfaceId={interface_id}"
            f"&language={DataQueryClient.language}&clientversion={DataQueryClient.clientVersion}"
        )

        for key, value in params.items():
            fetch_url += f"&{key}={value}"

        return fetch_url

    def _do_request(
        self, fetch_url: str, response_data: RetArray2D or RetDataBlock or RetFilesInfo
    ) -> bytes or None:
        try:
            response = requests.get(
                fetch_url,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            response_content = response.content

        except requests.exceptions.RequestException as e:  # http error
            print(f"Error retrieving data: {e}")
            response_data.request.errorCode = self.OTHER_ERROR
            response_data.request.errorMessage = "Error retrieving data"
            return None

        if DataQueryClient.getwayFlag in response_content:  # 网关错误
            getway_info = json.loads(response_content)
            if getway_info is None:
                response_data.request.errorCode = self.OTHER_ERROR
                response_data.request.errorMessage = (
                    "parse getway return string error:" + response_content
                )
            else:
                response_data.request.errorCode = getway_info["returnCode"]
                response_data.request.errorMessage = getway_info["returnMessage"]
            return None
        return response_content

    def _download_file(
        self, file_url: str, save_file: str or pathlib.Path
    ) -> (int, str):
        """
        下载文件
        """
        try:
            response = requests.get(file_url, stream=True)
            response_content = response.content
            if DataQueryClient.getwayFlag in response_content:  # 网关错误
                getway_info = json.loads(response_content)
                if getway_info is None:
                    return self.OTHER_ERROR, "parse getway return string error!"
                else:
                    return getway_info["returnCode"], getway_info["returnMessage"]

            with open(save_file, "wb") as f:
                f.write(response_content)

        except requests.exceptions.RequestException as e:  # http error
            return self.OTHER_ERROR, "request error"
        except IOError:
            return self.OTHER_ERROR, "create file error"

        return 0, None
