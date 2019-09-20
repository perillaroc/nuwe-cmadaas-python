#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
data store interface class
Created on 2016年3月28日
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr

Created on 2019年3月6日
@author: wufy
"""

import configparser
import json
import os
import socket
import sys
import uuid
from io import StringIO
from shutil import copyfile

import pycurl

from cma.music import DataFormatUtils, apiinterface_pb2
from cma.music.MusicDataBean import RequestInfo


class DataStoreClient(object):
    """
    data store interface class
    """

    language = "Python"
    # 客户端语言
    clientVersion = "V2.0.0"
    # 客户端版本
    getwayFlag = '"flag":"slb"'

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

        # 获取存储挂载方式，0文件将上传到服务端，1文件通过本地挂载盘写到服务端
        self.storeBackstage = cf.get("Pb", "music_store_backstage")
        if self.storeBackstage == 1:
            self.localMount = cf.get("Pb", "music_local_mount")  # 本地挂载目录对应位置
            self.serverMount = cf.get("Pb", "music_server_mount")  # 服务端挂载目录位置
        # 本机IP
        self.clientIp = socket.gethostbyname(socket.gethostname())
        self.basicUrl_write = "http://%s:%s/music-ws/write?serviceNodeId=%s&"
        self.basicUrl_upload = (
            "http://%s:%s/music-ws/upload?serviceNodeId=%s&fileName=%s&"
        )
        # return error code
        self.OTHER_ERROR = -10001
        # 其他异常

    def callAPI_to_storeArray2D(
        self, userId, pwd, interfaceId, params, inArray2D, serverId=None
    ):
        """
                     要素写入接口
        """
        # 所要调用的方法名称   打印该函数名称
        method = sys._getframe().f_code.co_name
        # print 'func.__name__: ' + method

        requestInfo = self.callAPI_to_storeArray2D_FileInfo(
            userId, pwd, interfaceId, serverId, params, method, inArray2D, None
        )

        return requestInfo

    def callAPI_to_storeFile(
        self,
        userId,
        pwd,
        interfaceId,
        params,
        inArray2D,
        inFilePaths,
        serverId=None,
        isBackstage=0,
        localMountPath="",
        serverMountPath="",
    ):
        if isBackstage == 1:
            if (localMountPath is None) or (serverMountPath is None):
                self.storeBackstageCur = isBackstage
                self.localMountCur = self.localMountPath
                self.serverMountPathCur = self.serverMountPath
            else:
                self.storeBackstageCur = isBackstage
                self.localMountCur = localMountPath
                self.serverMountPathCur = serverMountPath
        else:
            self.storeBackstageCur = isBackstage

        requestInfo = RequestInfo()
        # 所要调用的方法名称   打印该函数名称
        method = sys._getframe().f_code.co_name
        # print 'func.__name__: ' + method
        flagIsDelete = 0  # 是否为文件索引删除
        # 如果inArray2D为空，则返回
        if (inArray2D == None) or (len(inArray2D) == 0):
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Input data cant null!"
            return requestInfo

        inArray2DSize = len(inArray2D)
        fileNum = 0
        # 根据判断inFilePaths是否为空，调用不同方法 ,为空这删除文件索引信息，不为空则写入文件
        if (inFilePaths == None) or (len(inFilePaths) == 0):
            flagIsDelete = 1
        else:
            fileNum = len(inFilePaths)
            if inArray2DSize != fileNum or inArray2DSize == 0 or fileNum == 0:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = "Error:Input data number not right!"
                return requestInfo

        if flagIsDelete == 1:  # 删除文件索引信息
            return self.callAPI_to_storeArray2D_FileInfo(
                userId, pwd, interfaceId, serverId, params, method, inArray2D, None
            )
        else:
            # 获得文件大小(该二维数组中的所有文件大小)
            fileSize = self.getdirsize(inFilePaths)
            if fileSize <= 0:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = "Error:Input files can't exist empty file!"
                return requestInfo
            else:
                # http传输
                copyResult = []  # 传输是否成功
                httpTempNames = []
                utils = DataFormatUtils.Utils()
                for k in range(fileNum):
                    copyResult = []
                    uuidTemp = uuid.uuid1()
                    uploadFileName = "music_python_%d_%s" % (k, uuidTemp)
                    httpTempNames.append(uploadFileName)
                    fullFileName = inFilePaths[k]
                    if isBackstage == 1:  # 通过本地挂载盘写到服务端
                        strDesFile = self.localMountPathCur
                        strDesFile = strDesFile + os.sep + uploadFileName
                        copyResult = utils.copyFile(fullFileName, strDesFile)
                    else:  # 文件将上传到服务端
                        basicUrl = self.basicUrl_upload % (
                            self.serverIp,
                            self.serverPort,
                            self.serverId,
                            uploadFileName,
                        )
                        uploadUrl = basicUrl
                        uploadUrl += "&userId=%s" % userId
                        uploadUrl += "&pwd=%s" % pwd
                        print(uploadUrl)
                        copyResult = self.uploadFile(
                            uploadUrl, fullFileName, self.connTimeout, self.readTimeout
                        )
                    if copyResult[0] == False:
                        if copyResult[1].__contains__(
                            DataStoreClient.getwayFlag
                        ):  # 网关错误
                            getwayInfo = json.loads(copyResult[1])
                            if getwayInfo is None:
                                requestInfo.errorCode = self.OTHER_ERROR
                                requestInfo.errorMessage = (
                                    "parse getway return string error!"
                                )
                            else:
                                requestInfo.errorCode = getwayInfo["returnCode"]
                                requestInfo.errorMessage = getwayInfo["returnMessage"]
                            return requestInfo
                        else:
                            requestInfo.errorCode = self.OTHER_ERROR
                            requestInfo.errorMessage = (
                                "upload file fail:" + copyResult[1]
                            )
                            return requestInfo
                    # else:
                    # print 'upload file success:'+ fullFileName

            return self.callAPI_to_storeArray2D_FileInfo(
                userId,
                pwd,
                interfaceId,
                serverId,
                params,
                method,
                inArray2D,
                httpTempNames,
            )

    def callAPI_to_storeSerializedStr(
        self, userId, pwd, interfaceId, params, inString, serverId=None
    ):
        """
                    写入序列化字符串
        """
        # 1.1 所要调用的方法名称   打印该函数名称
        # method = 'callAPI_to_storeSerializedStr'
        method = sys._getframe().f_code.co_name
        # print 'func.__name__: ' + method
        # 2.1 二维数组 等同于list列表： [[ "20150114060000,54323;20150114060000,54326"]]
        # 2.1.1 二维数组的第二维
        inArray2D_1 = []
        inArray2D_1.append(inString)
        # 2.1.2 二维数组的第一维
        inArray2D = []
        inArray2D.append(inArray2D_1)
        requestInfo = self.callAPI_to_storeArray2D_FileInfo(
            userId, pwd, interfaceId, serverId, params, method, inArray2D, None
        )
        return requestInfo

    def callAPI_to_storeGridData(
        self, userId, pwd, interfaceId, params, inGridData, serverId=None
    ):
        """
                     写入格点数据
        """
        requestInfo = RequestInfo()
        method = "callAPI_to_storeGridData"  # 调用函数（方法）名称
        if (interfaceId == "saveGridData") and (inGridData.attributes is None):
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Input data attributes can't null!"
            return requestInfo

        if (inGridData.data is not None) and (len(inGridData.data) > 0):  # 不是删除
            if inGridData.pointFlag != 0:  # 点更新
                if (len(inGridData.lats) != len(inGridData.lons)) or (
                    len(inGridData.data) != len(inGridData.lons)
                ):
                    requestInfo.errorCode = self.OTHER_ERROR
                    requestInfo.errorMessage = "Input data size is wrong!"
                    return requestInfo
            else:
                if len(inGridData.data) != (
                    ((int)(inGridData.lats[0] + 0.5))
                    * ((int)(inGridData.lons[0] + 0.5))
                ):
                    requestInfo.errorCode = self.OTHER_ERROR
                    requestInfo.errorMessage = "Input data size is wrong!"
                    return requestInfo

        return self.callAPI_to_storeGridDataInfo(
            userId, pwd, interfaceId, method, params, inGridData, serverId
        )

    def callAPI_to_storeBlockData(
        self, userId, pwd, interfaceId, params, attributes, BlockData, serverId=None
    ):
        """
                     写入数据块
        """
        requestInfo = RequestInfo()
        method = "callAPI_to_storeBlockData"
        # 调用函数（方法）名称
        if ((interfaceId == "saveBlockData") or (interfaceId == "saveBlockData")) and (
            attributes is None
        ):
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Input data attributes can't null!"
            return requestInfo

        return self.callAPI_to_storeBlockDataInfo(
            userId, pwd, interfaceId, method, params, attributes, BlockData, serverId
        )

    def callAPI_to_storeArray2D_FileInfo(
        self,
        userId,
        pwd,
        interfaceId,
        serverId,
        params,
        method,
        inArray2D,
        inFilePaths=None,
    ):
        """
                     写入二维数据或文件信息
        """
        requestInfo = RequestInfo()
        # 如果inArray2D为空，则返回
        if (inArray2D == None) or (len(inArray2D) == 0):
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Input data cant null!"
            return requestInfo

        # 格式转换，生成Music的结果的对象
        utils = DataFormatUtils.Utils()
        # 根据判断inFilePaths是否为空，调用不同方法
        storeString = ""
        if (inFilePaths == None) or (len(inFilePaths) == 0):  # 非文件
            storeString = self.getPbStoreArray2DString(inArray2D, 0, None)
        elif inFilePaths is not None:
            fileRow = len(inFilePaths)
            array2DRow = len(inArray2D)
            if fileRow != array2DRow:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = (
                    "Input fileinfo and file number does not match !"
                )
                return requestInfo
            storeString = self.getPbStoreArray2DString(inArray2D, 1, inFilePaths)

        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)

        try:
            buf = StringIO.StringIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.POST, 1)
            storeNewString = "postdata=" + storeString
            response.setopt(pycurl.POSTFIELDS, storeNewString)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Error retrieving data"
            return requestInfo

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataStoreClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = "parse getway return string error!"
            else:
                requestInfo.errorCode = getwayInfo["returnCode"]
                requestInfo.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbRequestInfo = apiinterface_pb2.RequestInfo()
            pbRequestInfo.ParseFromString(RetByteArraydata)
            # 格式转换，生成music的结果
            utils = DataFormatUtils.Utils()
            requestInfo = utils.getRequestInfo(pbRequestInfo)

        return requestInfo

    def getConcateUrl(self, userId, pwd, interfaceId, params, serverId, method):
        """
                     将请求参数拼接为url 
        """
        if serverId is None:
            serverId = self.serverId
        # 初始化，并添加要拼接字符串的数据
        basicUrl = self.basicUrl_write % (self.serverIp, self.serverPort, serverId)
        finalUrl = StringIO.StringIO()
        finalUrl.write(basicUrl)
        finalUrl.write("method=" + method)
        finalUrl.write("&userId=" + userId)
        finalUrl.write("&pwd=" + pwd)
        finalUrl.write("&interfaceId=" + interfaceId)
        finalUrl.write("&language=" + DataStoreClient.language)
        finalUrl.write("&clientversion=" + DataStoreClient.clientVersion)
        # params从字典型数据转为字符串型，并拼接到finallUrl中
        for key, value in params.items():
            finalUrl.write("&%s=%s" % (key, value))

        # 返回finalUrl中的所有数据；并关闭对象 释放内存
        newUrl = finalUrl.getvalue()
        finalUrl.close()

        return newUrl

    def getdirsize(self, inFilePaths):
        """
                    获得文件大小(该二维数组中的所有文件大小)
        """
        size = 0
        for files in inFilePaths:
            size += os.path.getsize(files)
        return size

    def copyFile(self, srcFileName, desFileName):
        """
                     拷贝文件
        """
        if (srcFileName is None) or (desFileName is None):
            return (False, "srcFileName or desFileName is None")
        try:
            copyfile(srcFileName, desFileName)
        except IOError as e:
            return (False, "copy file error: %s" % e)
        except:
            return (False, "copy file error: %s" % sys.exc_info())

        return (True, "")

    def getPbStoreArray2DString(self, inArray2D, iFlag, inFilePaths):
        """
                     获取写入字符串
        """
        # 由StoreArray2D对象生成storeInfos
        pbStoreArray2D = apiinterface_pb2.StoreArray2D()

        # 获得inArray2D行列
        row = len(inArray2D)
        col = len(inArray2D[0])
        # 设置storeInfos的属性值
        pbStoreArray2D.row = row
        pbStoreArray2D.col = col
        pbStoreArray2D.fileflag = iFlag
        if iFlag == 1:
            pbStoreArray2D.is_backstage = self.storeBackstageCur
            if self.storeBackstageCur == 1:
                pbStoreArray2D.client_mount_path = self.localMountCur
                pbStoreArray2D.server_mount_path = self.serverMountPathCur

        # 日期 和 站点
        for i in range(row):
            for j in range(col):
                pbStoreArray2D.data.append(inArray2D[i][j])

        # 上传文件时的本地路径
        if iFlag == 1:
            for i in range(len(inFilePaths)):
                pbStoreArray2D.filenames.append(inFilePaths[i])

        return pbStoreArray2D.SerializeToString()

    def callAPI_to_storeGridDataInfo(
        self, userId, pwd, interfaceId, method, params, inGridData, serverId=None
    ):
        """
                     写入格点数据信息
        """
        # 生成music的RequestInfo结果的对象
        requestInfo = RequestInfo()
        pbStoreGridData = apiinterface_pb2.StoreGridData()
        attributes = inGridData.attributes
        for i in range(len(attributes)):
            pbStoreGridData.attributes.append(attributes[i])
        pbStoreGridData.pointflag = inGridData.pointFlag
        lats = inGridData.lats
        if len(lats) > 0:
            for i in range(len(lats)):
                pbStoreGridData.Lats.append(lats[i])
        lons = inGridData.lons
        if len(lons) > 0:
            for i in range(len(lons)):
                pbStoreGridData.Lons.append(lons[i])
        data = inGridData.data
        if len(data) > 0:
            for i in range(len(data)):
                pbStoreGridData.datas.append(data[i])

        storeString = pbStoreGridData.SerializeToString()

        # 写入数据到服务端时，返回的信息
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)

        try:
            buf = StringIO.StringIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.POST, 1)
            response.setopt(pycurl.HTTPHEADER, ["Content-Type:image/png"])
            response.setopt(pycurl.POSTFIELDSIZE, len(storeString))
            response.setopt(pycurl.POSTFIELDS, storeString)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Error retrieving data"
            return requestInfo

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataStoreClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = "parse getway return string error!"
            else:
                requestInfo.errorCode = getwayInfo["returnCode"]
                requestInfo.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbRequestInfo = apiinterface_pb2.RequestInfo()
            pbRequestInfo.ParseFromString(RetByteArraydata)
            # 格式转换，生成music的结果
            utils = DataFormatUtils.Utils()
            requestInfo = utils.getRequestInfo(pbRequestInfo)

        return requestInfo

    def callAPI_to_storeBlockDataInfo(
        self,
        userId,
        pwd,
        interfaceId,
        method,
        params,
        attributes,
        BlockData,
        serverId=None,
    ):
        """
                     写入数据块信息
        """
        # 生成music的RequestInfo结果的对象
        requestInfo = RequestInfo()
        pbStoreBlockData = apiinterface_pb2.StoreBlockData()
        for i in range(len(attributes)):
            pbStoreBlockData.attributes.append(attributes[i])
        pbStoreBlockData.data = BlockData
        storeString = pbStoreBlockData.SerializeToString()

        # 写入数据到服务端时，返回的信息
        # 构建music protobuf服务器地址，将请求参数拼接为url
        newUrl = self.getConcateUrl(userId, pwd, interfaceId, params, serverId, method)
        print("URL: " + newUrl)

        try:
            buf = StringIO.StringIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, newUrl)
            response.setopt(pycurl.POST, 1)
            response.setopt(pycurl.HTTPHEADER, ["Content-Type:image/png"])
            response.setopt(pycurl.POSTFIELDSIZE, len(storeString))
            response.setopt(pycurl.POSTFIELDS, storeString)
            response.setopt(pycurl.CONNECTTIMEOUT, self.connTimeout)
            response.setopt(pycurl.TIMEOUT, self.readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            # response.setopt(pycurl.WRITEDATA, value)
            response.perform()
            response.close()
        except:  # http error
            print("Error retrieving data")
            requestInfo.errorCode = self.OTHER_ERROR
            requestInfo.errorMessage = "Error retrieving data"
            return requestInfo

        RetByteArraydata = buf.getvalue()
        if RetByteArraydata.__contains__(DataStoreClient.getwayFlag):  # 网关错误
            getwayInfo = json.loads(RetByteArraydata)
            if getwayInfo is None:
                requestInfo.errorCode = self.OTHER_ERROR
                requestInfo.errorMessage = "parse getway return string error!"
            else:
                requestInfo.errorCode = getwayInfo["returnCode"]
                requestInfo.errorMessage = getwayInfo["returnMessage"]
        else:  # 服务端返回结果
            # 反序列化为proto的结果
            pbRequestInfo = apiinterface_pb2.RequestInfo()
            pbRequestInfo.ParseFromString(RetByteArraydata)
            # 格式转换，生成music的结果
            utils = DataFormatUtils.Utils()
            requestInfo = utils.getRequestInfo(pbRequestInfo)

        return requestInfo

    def uploadFile(self, uploadUrl, fullFileName, connTimeout, readTimeout):
        """
                    上传文件
        """
        try:
            f = open(fullFileName, "rb")
            data = f.read()
            f.close()
            buf = StringIO.StringIO()
            response = pycurl.Curl()
            response.setopt(pycurl.URL, uploadUrl)
            response.setopt(pycurl.POST, 1)
            response.setopt(pycurl.HTTPHEADER, ["Content-Type:image/png"])
            response.setopt(pycurl.CONNECTTIMEOUT, connTimeout)
            response.setopt(pycurl.TIMEOUT, readTimeout)
            response.setopt(pycurl.WRITEFUNCTION, buf.write)
            response.setopt(pycurl.POSTFIELDSIZE, len(data))
            response.setopt(pycurl.POSTFIELDS, data)
            response.perform()
            response.close()
            RetByteArraydata = buf.getvalue()
        except:
            print("Error retrieving data")
            return (False, "Error retrieving data")

        if RetByteArraydata.__contains__(DataStoreClient.getwayFlag):  # 网关错误
            return (False, RetByteArraydata)

        return (True, RetByteArraydata)
