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
        error_code: int = 0,
        error_message: str = "",
        request_elems: str = "",
        request_params: str = "",
        request_time: str = "",
        response_time: str = "",
        row_count: int = 0,
        take_time: int = 0,
    ):
        self.error_code = error_code  # 错误编码
        self.error_message = error_message  # 错误信息
        self.request_elems = request_elems  # 请求要素
        self.request_params = request_params  # 请求参数
        self.request_time = request_time  # 请求时间
        self.response_time = response_time  # 响应时间
        self.rowCount = row_count  # 返回行数
        self.takeTime = take_time  # 耗时

    def stringify(self):
        return f"""request = {{
    error_code:"{self.error_code}"
    error_message:"{self.error_message}"
    request_elems:"{self.request_elems}"
    request_params:"{self.request_params}"
    request_time:"{self.request_time}"
    response_time:"{self.response_time}"
    rowCount:"{self.rowCount}"
    takeTime:"{self.takeTime}"
}}"""

    def __str__(self):
        return self.stringify()

    __repr__ = __str__


class RetArray2D(object):
    """
    返回二维数据
    """

    def __init__(self, data=None, request=None, row=0, col=0, element_names=None):
        self.data = data  # 返回检索结果
        if request is None:
            self.request = RequestInfo()
        else:
            self.request = request  # 请求信息
        self.row = row  # 检索结果行数
        self.col = col  # 检索结果列数
        self.element_names = element_names  # 要素名称

    def stringify(self):
        ret_data = f"""data = 
{{
{self.data}
}}
"""
        return f"""{{
{ret_data}
request={self.request}
row={self.row}
col={self.col}
element_names={self.element_names}
}}"""

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
        start_lat=0.0,
        start_lon=0.0,
        end_lat=0.0,
        end_lon=0.0,
        lat_count=0,
        lon_count=0,
        lon_step=0.0,
        lat_step=0.0,
        units="",
        user_ele_name="",
        lats=None,
        lons=None,
    ):
        self.data = data  # 返回格点数据
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.start_lat = start_lat  # 起始纬度
        self.start_lon = start_lon  # 起始经度
        self.end_lat = end_lat  # 结束纬度
        self.end_lon = end_lon  # 结束经度
        self.lat_count = lat_count  # 纬度计数
        self.lon_count = lon_count  # 经度计数
        self.lon_step = lon_step  # 经度步长
        self.lat_step = lat_step  # 纬度步长
        self.units = units  # 单位
        self.user_ele_name = user_ele_name  # 要素名称
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
        start_lat=0.0,
        start_lon=0.0,
        end_lat=0.0,
        end_lon=0.0,
        lat_count=0,
        lon_count=0,
        lon_step=0.0,
        lat_step=0.0,
        units="",
        user_ele_name="",
        lats=None,
        lons=None,
    ):
        self.data = data  # 返回格点数据
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.start_lat = start_lat  # 起始纬度
        self.start_lon = start_lon  # 起始经度
        self.end_lat = end_lat  # 结束纬度
        self.end_lon = end_lon  # 结束经度
        self.lat_count = lat_count  # 纬度计数
        self.lon_count = lon_count  # 经度计数
        self.lon_step = lon_step  # 经度步长
        self.lat_step = lat_step  # 纬度步长
        self.units = units  # 单位
        self.user_ele_name = user_ele_name  # 要素名称
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
        start_lat=0.0,
        start_lon=0.0,
        end_lat=0.0,
        end_lon=0.0,
        lat_count=0,
        lon_count=0,
        lon_step=0.0,
        lat_step=0.0,
        u_ele_name="",
        v_ele_name="",
        lats=None,
        lons=None,
    ):
        if request is None:
            self.request = RequestInfo()  # 请求信息
        else:
            self.request = request  #
        self.start_lat = start_lat  # 起始纬度
        self.start_lon = start_lon  # 起始经度
        self.end_lat = end_lat  # 结束纬度
        self.end_lon = end_lon  # 结束经度
        self.lat_count = lat_count  # 纬度计数
        self.lon_count = lon_count  # 经度计数
        self.lon_step = lon_step  # 经度步长
        self.lat_step = lat_step  # 纬度步长
        self.u_ele_name = u_ele_name  # u分量的要素名称
        self.v_ele_name = v_ele_name  # V分量的要素名称
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
        file_name="",
        save_path="",
        suffix="",
        size="",
        file_url="",
        img_base64="",
        attributes=None,
    ):
        self.file_name = file_name  # 文件名
        self.save_path = save_path  # 文件全路径
        self.suffix = suffix  # 文件格式
        self.size = size  # 文件大小
        self.file_url = file_url  # 文件下载url
        self.img_base64 = img_base64
        self.attributes = []  # 其他文件索引(字段)信息，不包含上面已有信息
        if attributes is not None:
            for i in range(len(attributes)):
                self.attributes.append(attributes[i])

    def stringify(self):
        return f"""fileInfo = {{
    file_name:"{self.file_name}"
    save_path:"{self.save_path}"
    suffix:"{self.suffix}"
    size:"{self.size}"
    file_url:"{self.file_url}"
    img_base64:"{self.img_base64}"
    attributes:"{self.attributes}"
}}"""

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
        self.file_infos = []

    def stringify(self):
        print_str = ""
        for i in range(len(self.file_infos)):
            print_str += str(self.file_infos[i].fileName)
            print(str(self.file_infos[i].fileName))
            print_str += str(self.file_infos[i].savePath)
            print_str += str(self.file_infos[i].suffix)
            print_str += str(self.file_infos[i].size)
            print_str += str(self.file_infos[i].fileUrl)
            print_str += str(self.file_infos[i].imgBase64)
            print_str += str(self.file_infos[i].attributes)
        print(print_str)

        return print_str  # (self.fileInfos)

    def __str__(self):
        # return self.stringify()
        return str(self.file_infos)

    __repr__ = __str__


class RetDataBlock(object):
    def __init__(self, data_name="", byte_array=None, request=None):
        self.data_name = data_name
        self.byte_array = byte_array
        if request is None:
            self.request = RequestInfo()
        else:
            self.request = request


class StoreArray2D(object):
    def __init__(self, data="", row="", col="", file_flag="", file_names=None):
        self.data = data
        self.row = row
        self.col = col
        self.file_flag = file_flag
        self.file_names = file_names


class StoreGridData(object):
    def __init__(self, attributes=None, point_flag="", lats=None, lons=None, data=None):
        self.attributes = attributes
        self.point_flag = point_flag
        self.lats = lats
        self.lons = lons
        self.data = data


# End of module cma.music

__name__ = "cma"

# End of module cma
