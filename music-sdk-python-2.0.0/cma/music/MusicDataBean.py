#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr

Modified on 2019年3月10日
@author: wufy
"""

import sys

__name__ = "cma.music"
sys.setrecursionlimit(1500)


class RequestInfo(object):
    """
            请求信息
    """

    def __init__(
        self,
        errorCode=0,
        errorMessage="",
        requestElems="",
        requestParams="",
        requestTime="",
        responseTime="",
        rowCount=0,
        takeTime=0,
    ):
        self.errorCode = errorCode  # 错误编码
        self.errorMessage = errorMessage  # 错误信息
        self.requestElems = requestElems  # 请求要素
        self.requestParams = requestParams  # 请求参数
        self.requestTime = requestTime  # 请求时间
        self.responseTime = responseTime  # 响应时间
        self.rowCount = rowCount  # 返回行数
        self.takeTime = takeTime  # 耗时

    def stringify(self):
        return (
            'request = {\n errorCode:"%s"\n errorMessage:"%s"\n requestElems:"%s"\n requestParams:"%s"\n requestTime:"%s"\n responseTime:"%s"\n rowCount:"%s"\n takeTime:"%s"\n}'
            % (
                self.errorCode,
                self.errorMessage,
                self.requestElems,
                self.requestParams,
                self.requestTime,
                self.responseTime,
                self.rowCount,
                self.takeTime,
            )
        )

    def __str__(self):
        # return 'request =\n{\n%s}' % (self.errorCode)
        return self.stringify()

    __repr__ = __str__


class RetArray2D(object):
    """
            返回二维数据
    """

    def __init__(self, data=None, request=None, row=0, col=0, elementNames=None):
        self.data = data  # 返回检索结果
        if request is None:
            self.request = RequestInfo()
        else:
            self.request = request  # 请求信息
        self.row = row  # 检索结果行数
        self.col = col  # 检索结果列数
        self.elementNames = elementNames  # 要素名称

    def stringify(self):
        retData = "data = \n{\n%s\n}\n" % (self.data)
        return "{\n%s\nrequest=%s\nrow=%s\ncol=%s\nelementNames=%s\n}" % (
            retData,
            self.request,
            self.row,
            self.col,
            self.elementNames,
        )

    def __str__(self):
        return self.stringify()

    __repr__ = __str__


class RetGridArray2D(object):
    """
            返回格点结果
    """

    def __init__(
        self,
        data=None,
        request=None,
        startLat=0.0,
        startLon=0.0,
        endLat=0.0,
        endLon=0.0,
        latCount=0,
        lonCount=0,
        lonStep=0.0,
        latStep=0.0,
        units="",
        userEleName="",
        lats=None,
        lons=None,
    ):
        self.data = data  # 返回格点数据
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.startLat = startLat  # 起始纬度
        self.startLon = startLon  # 起始经度
        self.endLat = endLat  # 结束纬度
        self.endLon = endLon  # 结束经度
        self.latCount = latCount  # 纬度计数
        self.lonCount = lonCount  # 经度计数
        self.lonStep = lonStep  # 经度步长
        self.latStep = latStep  # 纬度步长
        self.units = units  # 单位
        self.userEleName = userEleName  # 要素名称
        self.lats = lats  # 维度值
        self.lons = lons  # 经度值


class RetGridScalar2D(object):
    """
            返回格点标量结果
    """

    def __init__(
        self,
        data=None,
        request=None,
        startLat=0.0,
        startLon=0.0,
        endLat=0.0,
        endLon=0.0,
        latCount=0,
        lonCount=0,
        lonStep=0.0,
        latStep=0.0,
        units="",
        userEleName="",
        lats=None,
        lons=None,
    ):
        self.data = data  # 返回格点数据
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.startLat = startLat  # 起始纬度
        self.startLon = startLon  # 起始经度
        self.endLat = endLat  # 结束纬度
        self.endLon = endLon  # 结束经度
        self.latCount = latCount  # 纬度计数
        self.lonCount = lonCount  # 经度计数
        self.lonStep = lonStep  # 经度步长
        self.latStep = latStep  # 纬度步长
        self.units = units  # 单位
        self.userEleName = userEleName  # 要素名称
        self.lats = lats  # 维度值
        self.lons = lons  # 经度值


class RetGridVector2D(object):
    """
            返回格点矢量结果
    """

    def __init__(
        self,
        u_datas=None,
        v_datas=None,
        request=None,
        startLat=0.0,
        startLon=0.0,
        endLat=0.0,
        endLon=0.0,
        latCount=0,
        lonCount=0,
        lonStep=0.0,
        latStep=0.0,
        u_EleName="",
        v_EleName="",
        lats=None,
        lons=None,
    ):
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.startLat = startLat  # 起始纬度
        self.startLon = startLon  # 起始经度
        self.endLat = endLat  # 结束纬度
        self.endLon = endLon  # 结束经度
        self.latCount = latCount  # 纬度计数
        self.lonCount = lonCount  # 经度计数
        self.lonStep = lonStep  # 经度步长
        self.latStep = latStep  # 纬度步长
        self.u_EleName = u_EleName  # u分量的要素名称
        self.v_EleName = v_EleName  # V分量的要素名称
        self.lats = lats  # 维度值
        self.lons = lons  # 经度值
        self.u_datas = u_datas  # u分量的数据值
        self.v_datas = v_datas  # v分量的数据值


class FileInfo(object):
    """
            文件索引信息
    """

    def __init__(
        self,
        fileName="",
        savePath="",
        suffix="",
        size="",
        fileUrl="",
        imgBase64="",
        attributes=None,
    ):
        self.fileName = fileName  # 文件名
        self.savePath = savePath  # 文件全路径
        self.suffix = suffix  # 文件格式
        self.size = size  # 文件大小
        self.fileUrl = fileUrl  # 文件下载url
        self.imgBase64 = imgBase64
        self.attributes = []  # 其他文件索引(字段)信息，不包含上面已有信息
        if attributes is not None:
            for i in range(len(attributes)):
                self.attributes.append(attributes[i])

    def stringify(self):
        return (
            'fileInfo = {\n fileName:"%s"\n savePath:"%s"\n suffix:"%s"\n size:"%s"\n fileUrl:"%s"\n imgBase64:"%s"\n attributes:"%s"\n }'
            % (
                self.fileName,
                self.savePath,
                self.suffix,
                self.size,
                self.fileUrl,
                self.imgBase64,
                self.attributes,
            )
        )

    def __str__(self):
        return self.stringify()

    __repr__ = __str__


class RetFilesInfo(object):
    """
           返回文件索引信息
    """

    def __init__(self, request=None, count=0):
        self.count = count
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request
        self.fileInfos = []

    def stringify(self):
        strr = ""
        for i in range(len(self.fileInfos)):
            strr += str(self.fileInfos[i].fileName)
            print(str(self.fileInfos[i].fileName))
            strr += str(self.fileInfos[i].savePath)
            strr += str(self.fileInfos[i].suffix)
            strr += str(self.fileInfos[i].size)
            strr += str(self.fileInfos[i].fileUrl)
            strr += str(self.fileInfos[i].imgBase64)
            strr += str(self.fileInfos[i].attributes)
        print(strr)

        return strr  # (self.fileInfos)

    def __str__(self):
        # return self.stringify()
        return str(self.fileInfos)

    __repr__ = __str__


"""       
class RetFilesInfo(object):
    def __init__(self, fileInfos=None, request=None, count=0):
        self.fileInfos = fileInfos
        self.count = count
        if request is None:
            self.request = RequestInfo()
        else:
            self.request = request
          
    def __str__(self):
        return 'fileInfos=%s\n request=%s\n count=%s\n' % (self.fileInfos,self.request,self.count)
        
    #__repr__ = __str__    
"""


class RetDataBlock(object):
    def __init__(self, dataName="", byteArray=None, request=None):
        self.dataName = dataName
        self.byteArray = byteArray
        if request is None:
            self.request = RequestInfo()
        else:
            self.request = request


class StoreArray2D(object):
    def __init__(self, data="", row="", col="", fileflag="", filenames=None):
        self.data = data
        self.row = row
        self.col = col
        self.fileflag = fileflag
        self.filenames = filenames


class StoreGridData(object):
    def __init__(self, attributes=None, pointFlag="", lats=None, lons=None, data=None):
        self.attributes = attributes
        self.pointFlag = pointFlag
        self.lats = lats
        self.lons = lons
        self.data = data


# End of module cma.music

__name__ = "cma"

# End of module cma
