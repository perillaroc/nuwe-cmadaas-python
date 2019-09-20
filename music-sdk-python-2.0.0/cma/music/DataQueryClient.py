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
from io import BytesIO, StringIO
from urllib.request import urlopen

import pycurl

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


class DataQueryClient(object):
    """
    data query interface class
    """

    language = "Python"
    # 客户端语言
    clientVersion = "V2.0.0"
    # 客户端版本
    getwayFlag = b'"flag":"slb"'

    # 网关返回错误标识

    def __init__(
        self,
        serverIp=None,
        serverPort=None,
        serviceNodeId=None,
        connTimeout=None,
        readTimeout=None,
        configFile=None,
    ):
        """
        Constructor
        """
        # get config file
        config = ""
        if configFile is not None:
            if not os.path.exists(configFile):
                raise RuntimeError("config file is not exist.")
            else:
                config = configFile
        else:
            defaultConfig = "client.config"
            if os.path.exists(defaultConfig):
                config = defaultConfig
            else:
                raise RuntimeError("default config file is not exist.")
        # read config file object
        cf = configparser.ConfigParser()
        cf.read(config)
        # get server IP
        if serverIp is None:
            self.serverIp = cf.get("Pb", "music_server")
        else:
            self.serverIp = serverIp
        # get server port
        if serverPort is None:
            self.serverPort = cf.getint("Pb", "music_port")
        else:
            self.serverPort = serverPort
        # get service Node ID
        if serviceNodeId is None:
            self.serverId = cf.get("Pb", "music_ServiceId")
        else:
            self.serverId = serviceNodeId
        # get connect time out and read time out
        if connTimeout is None:
            self.connTimeout = int(cf.get("Pb", "music_connTimeout"))
        else:
            if connTimeout.isdigit():
                self.connTimeout = int(connTimeout)
        # print self.connTimeout
        if readTimeout is None:
            self.readTimeout = int(cf.get("Pb", "music_readTimeout"))
        else:
            if readTimeout.isdigit():
                self.readTimeout = int(readTimeout)
        # print self.readTimeout

        # 本机IP
        self.clientIp = socket.gethostbyname(socket.gethostname())
        self.basicUrl = (
            "http://%s:%s/music-ws/api?serviceNodeId=%s&"
        )  # 数据读取URL(基本路径) http://ip:port/music-ws/api?serviceNodeId=serverId&

        # return error code
        self.OTHER_ERROR = -10001
        # 其他异常

    def callAPI_to_array2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     站点资料（要素）数据检索
        """
        retArray2D = RetArray2D()
        # 所要调用的方法名称
        method = "callAPI_to_array2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retArray2D.request.errorCode = self.OTHER_ERROR
            retArray2D.request.errorMessage = "Error retrieving data"
            return retArray2D

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retArray2D.request.errorCode = self.OTHER_ERROR
                retArray2D.request.errorMessage = (
                    "parse getway return string error:" + RetByteArraydata
                )
            else:
                retArray2D.request.errorCode = getwayInfo["returnCode"]
                retArray2D.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbRetArray2D = apiinterface_pb2.RetArray2D()
            pbRetArray2D.ParseFromString(RetByteArraydata)
            utils = DataFormatUtils.Utils()
            retArray2D = utils.getArray2D(pbRetArray2D)

        return retArray2D

    def callAPI_to_dataBlock(self, userId, pwd, interfaceId, params, serverId=None):
        """
                    数据块检索
        """
        retDataBlock = RetDataBlock()
        # 所要调用的方法名称
        method = "callAPI_to_dataBlock"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            retDataBlock.request.errorCode = self.OTHER_ERROR
            retDataBlock.request.errorMessage = "Error retrieving data"
            return retDataBlock

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retDataBlock.request.errorCode = self.OTHER_ERROR
                retDataBlock.request.errorMessage = "parse getway return string error!"
            else:
                retDataBlock.request.errorCode = getwayInfo["returnCode"]
                retDataBlock.request.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbDataBlock = apiinterface_pb2.RetDataBlock()
            pbDataBlock.ParseFromString(RetByteArraydata)
            # 格式转换
            utils = DataFormatUtils.Utils()
            retDataBlock = utils.getDataBlock(pbDataBlock)

        return retDataBlock

    def callAPI_to_gridArray2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     网格数据检索
        """
        retGridArray2D = RetGridArray2D()
        # 所要调用的方法名称
        method = "callAPI_to_gridArray2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retGridArray2D = utils.getGridArray2D(pbGridArray2D)

        return retGridArray2D

    def callAPI_to_fileList(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     文件存储信息列表检索
        """
        retFilesInfo = RetFilesInfo()
        # 所要调用的方法名称
        method = "callAPI_to_fileList"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retFilesInfo = utils.getRetFilesInfo(pbRetFilesInfo)

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
        if params.has_key("dataFormat") is False:
            params["dataFormat"] = dataFormat
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            return "Error retrieving data"

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataQueryClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                retStr = "parse getway return string error:" + RetByteArraydata.decode(
                    "utf8"
                )
            else:
                retStr = "getway error: returnCode=%s returnMessage=%s" % (
                    getwayInfo["returnCode"],
                    getwayInfo["returnMessage"],
                )
        else:  # 服务端返回结果
            # 反序列化为的结果string
            retStr = RetByteArraydata.decode("utf8")

        return retStr

    def callAPI_to_saveAsFile(
        self, userId, pwd, interfaceId, params, dataFormat, fileName, serverId=None
    ):
        """
                     把结果存成文件下载到本地（检索结果为要素，服务端保存为文件）
        """
        retFilesInfo = RetFilesInfo()
        # 所要调用的方法名称
        method = "callAPI_to_saveAsFile"
        # 添加数据格式
        if params.has_key("dataFormat") is False:
            params["dataFormat"] = dataFormat
        if fileName is None:
            retFilesInfo.request.errorCode = self.OTHER_ERROR
            retFilesInfo.request.errorMessage = "error:savePath can't null,the format is dir/file.formart(ex. /data/saveas.xml)"
            return retFilesInfo
        params["savepath"] = fileName
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retFilesInfo = utils.getRetFilesInfo(pbRetFilesInfo)
            # 将数据保存到本地
            if retFilesInfo:
                if retFilesInfo.request.errorCode == 0:
                    result = self.downloadFile(
                        retFilesInfo.fileInfos[0].fileUrl, fileName
                    )  # 下载文件
                    if result[0] != 0:
                        retFilesInfo.request.errorCode = result[0]
                        retFilesInfo.request.errorMessage = result[1]
                        return retFilesInfo

        return retFilesInfo

    def callAPI_to_downFile(
        self, userId, pwd, interfaceId, params, fileDir, serverId=None
    ):
        """
                    检索并下载文件
        """
        file_Dir = fileDir
        if file_Dir.endswith(os.sep):
            pass
        else:
            file_Dir = file_Dir + os.sep
        retFilesInfo = RetFilesInfo()
        # 所要调用的方法名称   打印该函数名称
        method = "callAPI_to_fileList"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retFilesInfo = utils.getRetFilesInfo(pbRetFilesInfo)

        if retFilesInfo:
            if retFilesInfo.request.errorCode == 0:
                for info in retFilesInfo.fileInfos:
                    result = self.downloadFile(info.fileUrl, file_Dir + info.fileName)
                    if result[0] != 0:
                        retFilesInfo.request.errorCode = result[0]
                        retFilesInfo.request.errorMessage = result[1]
                        return retFilesInfo
        return retFilesInfo

    def callAPI_to_downFile_ByUrl(self, fileURL, save_as):
        """
                    根据url下载文件
        """
        result = self.downloadFile(fileURL, save_as)
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
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retGridScalar2D = utils.getGridScalar2D(pbGridScalar2D)

        return retGridScalar2D

    def callAPI_to_gridVector2D(self, userId, pwd, interfaceId, params, serverId=None):
        """
                     网格矢量数据
        """
        retGridVector2D = RetGridVector2D()
        # 所要调用的方法名称
        method = "callAPI_to_gridVector2D"
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)
        try:
            buf = BytesIO()
            # buf = BytesIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
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
            retGridVector2D = utils.getGridVector2D(pbGridVector2D)

        return retGridVector2D

    def getConcateUrl(self, userId, pwd, interfaceId, params, serverId, method):
        """
                     将请求参数拼接为url 
        """
        if serverId is None:
            serverId = self.serverId
        # 初始化，并添加要拼接字符串的数据
        basicUrl = self.basicUrl % (self.serverIp, self.serverPort, serverId)
        finalUrl = StringIO()
        finalUrl.write(basicUrl)
        finalUrl.write("method=" + method)
        finalUrl.write("&userId=" + userId)
        finalUrl.write("&pwd=" + pwd)
        finalUrl.write("&interfaceId=" + interfaceId)
        finalUrl.write("&language=" + DataQueryClient.language)
        finalUrl.write("&clientversion=" + DataQueryClient.clientVersion)
        # params从字典型数据转为字符串型，并拼接到finallUrl中
        for key, value in params.items():
            finalUrl.write("&%s=%s" % (key, value))

        # 返回finalUrl中的所有数据；并关闭对象 释放内存
        newUrl = finalUrl.getvalue()
        finalUrl.close()

        return newUrl

    def downloadFile(self, fileUrl, saveFile):
        """
                    下载文件
        """
        try:
            response = urlopen(fileUrl)
            data = response.read()
            if data.__contains__(DataQueryClient.getwayFlag):  # 网关错误
                getwayInfo = json.loads(data)
                if getwayInfo is None:
                    return (self.OTHER_ERROR, "parse getway return string error!")
                else:
                    return (getwayInfo["returnCode"], getwayInfo["returnMessage"])
            else:
                with open(saveFile, "wb") as code:
                    code.write(data)
        except:
            return (self.OTHER_ERROR, "download file error")

        return (0, "")
