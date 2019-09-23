#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Modified in 2016/03/28
@author: xjunior

Modified in 2018/11/18
@author: wufeng & lr
"""
from cma.music import MusicDataBean
from cma.music import apiinterface_pb2 as pb


class Utils:
    """
    数据格式转换，protobuf结构和Music数据结构转换
    """

    def __init__(self):
        pass

    @classmethod
    def convert_to_dict(cls, obj) -> dict:
        """
        把Object对象转换成Dict对象
        """
        result = {}
        result.update(obj.__dict__)
        return result

    @classmethod
    def convert_to_dicts(cls, objs) -> list:
        """
        把对象列表转换为字典列表
        """
        obj_list = []

        for o in objs:
            d = {}
            d.update(o.__dict__)
            obj_list.append(d)

        return obj_list

    @classmethod
    def set_matrix(cls, rows: int, cols: int, data: list) -> list:
        """
        按行列转换数据为二维数组
        """
        matrix = [[0 for col in range(cols)] for row in range(rows)]
        for i in range(rows):
            matrix[i] = data[i * cols : i * cols + cols]

        return matrix

    @classmethod
    def set_request_info(
        cls, pb_request_info: pb.RequestInfo = None
    ) -> MusicDataBean.RequestInfo:
        return Utils.get_request_info(pb_request_info)

    @classmethod
    def get_request_info(
        cls, pb_request_info: pb.RequestInfo
    ) -> MusicDataBean.RequestInfo:
        """
        将protobuf类实例转换为music RequestInfo结构数据
        """
        request_info = MusicDataBean.RequestInfo(
            pb_request_info.errorCode,
            pb_request_info.errorMessage,
            pb_request_info.requestElems,
            pb_request_info.requestParams,
            pb_request_info.requestTime,
            pb_request_info.responseTime,
            pb_request_info.rowCount,
            pb_request_info.takeTime,
        )

        return request_info

    @classmethod
    def get_array_2d(cls, pb_ret_array_2d: pb.RetArray2D) -> MusicDataBean.RetArray2D:
        """
        将protobuf类实例转换为music RetArray2D结构数据
        """
        ret_array_2d = MusicDataBean.RetArray2D(
            pb_ret_array_2d.data, pb_ret_array_2d.request
        )

        # 如果该结果数据存在，则将获取的数据，转换为二维数组格式
        if ret_array_2d:
            # 将获取请求信息，转换为子类对象，进行封装
            ret_array_2d.request = Utils.set_request_info(pb_ret_array_2d.request)
            ret_array_2d.element_names = pb_ret_array_2d.elementNames
            ret_code = ret_array_2d.request.error_code  # 获得错误编码
            # 返回码为0，表示返回结果成功
            if ret_code == 0:
                rows = ret_array_2d.request.rowCount  # 获得数据的行数
                ret_array_2d.row = rows
                cnt = len(ret_array_2d.data)  # 获得所有数据的个数
                # print 'cnt:' + str(cnt)
                # print 'row:' + str(rows)
                cols = int(cnt / rows)  # 获得数据的列数
                ret_array_2d.col = cols
                # print 'col:' + str(cols) + '\n'
                # 将获取的数据，转换为二维数组格式
                ret_array_2d.data = Utils.set_matrix(rows, cols, ret_array_2d.data)

        return ret_array_2d

    @classmethod
    def get_data_block(
        cls, pb_ret_data_block: pb.RetDataBlock
    ) -> MusicDataBean.RetDataBlock:
        """
        将protobuf类实例转换为music RetDataBlock结构数据
        """
        ret_data_block = MusicDataBean.RetDataBlock(
            pb_ret_data_block.dataName,
            pb_ret_data_block.byteArray,
            pb_ret_data_block.request,
        )
        if ret_data_block is not None:
            ret_data_block.request = Utils.set_request_info(pb_ret_data_block.request)

        return ret_data_block

    @classmethod
    def get_grid_array_2d(
        cls, pb_ret_grid_array_2d: pb.RetGridArray2D
    ) -> MusicDataBean.RetGridArray2D:
        """
        将protobuf类实例转换为music RetGridArray2D结构数据
        """
        ret_grid_array_2d = MusicDataBean.RetGridArray2D(
            pb_ret_grid_array_2d.data, pb_ret_grid_array_2d.request
        )
        # 如果该结果数据存在，则将获取的数据，转换为二维数组格式
        if ret_grid_array_2d:
            ret_grid_array_2d.request = Utils.set_request_info(
                pb_ret_grid_array_2d.request
            )
            ret_code = ret_grid_array_2d.request.error_code
            if ret_code == 0:
                ret_grid_array_2d.start_lat = pb_ret_grid_array_2d.startLat
                ret_grid_array_2d.start_lon = pb_ret_grid_array_2d.startLon
                ret_grid_array_2d.end_lat = pb_ret_grid_array_2d.endLat
                ret_grid_array_2d.end_lon = pb_ret_grid_array_2d.endLon
                ret_grid_array_2d.lat_count = pb_ret_grid_array_2d.latCount
                ret_grid_array_2d.lon_count = pb_ret_grid_array_2d.lonCount
                ret_grid_array_2d.lon_step = pb_ret_grid_array_2d.lonStep
                ret_grid_array_2d.lat_step = pb_ret_grid_array_2d.latStep
                if pb_ret_grid_array_2d.lats is None:
                    start_lat = ret_grid_array_2d.start_lat
                    lat_step = ret_grid_array_2d.lat_step
                    for i in range(ret_grid_array_2d.lat_count):
                        ret_grid_array_2d.lats.append(start_lat + i * lat_step)
                else:
                    ret_grid_array_2d.lats = pb_ret_grid_array_2d.lats
                if pb_ret_grid_array_2d.lons is None:
                    start_lon = ret_grid_array_2d.start_lon
                    lon_step = ret_grid_array_2d.lon_step
                    for i in range(ret_grid_array_2d.lon_count):
                        ret_grid_array_2d.lons.append(start_lon + i * lon_step)
                else:
                    ret_grid_array_2d.lons = pb_ret_grid_array_2d.lons
                ret_grid_array_2d.units = pb_ret_grid_array_2d.units
                ret_grid_array_2d.user_ele_name = pb_ret_grid_array_2d.userEleName
                rows = ret_grid_array_2d.request.rowCount  # 获得数据的行数
                data_len = len(ret_grid_array_2d.data)  # 获得所有数据的个数
                cols = data_len / rows
                ret_grid_array_2d.data = Utils.set_matrix(
                    rows, cols, ret_grid_array_2d.data
                )

        return ret_grid_array_2d

    @classmethod
    def get_grid_scalar_2d(
        cls, pb_ret_grid_scalar_2d: pb.RetGridScalar2D
    ) -> MusicDataBean.RetGridScalar2D:
        """
        将protobuf类实例转换为music RetGridScalar2D结构数据
        """
        ret_grid_scalar_2d = MusicDataBean.RetGridScalar2D(
            pb_ret_grid_scalar_2d.datas, pb_ret_grid_scalar_2d.request
        )
        # 如果该结果数据存在，则将获取的数据，转换为二维数组格式
        if ret_grid_scalar_2d:
            ret_grid_scalar_2d.request = Utils.set_request_info(
                pb_ret_grid_scalar_2d.request
            )
            ret_code = ret_grid_scalar_2d.request.error_code
            if ret_code == 0:
                ret_grid_scalar_2d.start_lat = pb_ret_grid_scalar_2d.startLat
                ret_grid_scalar_2d.start_lon = pb_ret_grid_scalar_2d.startLon
                ret_grid_scalar_2d.end_lat = pb_ret_grid_scalar_2d.endLat
                ret_grid_scalar_2d.end_lon = pb_ret_grid_scalar_2d.endLon
                ret_grid_scalar_2d.lat_count = pb_ret_grid_scalar_2d.latCount
                ret_grid_scalar_2d.lon_count = pb_ret_grid_scalar_2d.lonCount
                ret_grid_scalar_2d.lon_step = pb_ret_grid_scalar_2d.lonStep
                ret_grid_scalar_2d.lat_step = pb_ret_grid_scalar_2d.latStep
                ret_grid_scalar_2d.lats = pb_ret_grid_scalar_2d.lats
                ret_grid_scalar_2d.lons = pb_ret_grid_scalar_2d.lons
                ret_grid_scalar_2d.units = pb_ret_grid_scalar_2d.units
                ret_grid_scalar_2d.user_ele_name = pb_ret_grid_scalar_2d.userEleName
                #                 rows = ret_grid_scalar_2d.request.rowCount    # 获得数据的行数
                #                 dataLen = len(ret_grid_scalar_2d.data)        # 获得所有数据的个数
                #                 cols = dataLen/rows
                #                 ret_grid_scalar_2d.data = self.set_matrix(rows,cols,ret_grid_scalar_2d.data)
                ret_grid_scalar_2d.data = Utils.set_matrix(
                    ret_grid_scalar_2d.lat_count,
                    ret_grid_scalar_2d.lon_count,
                    ret_grid_scalar_2d.data,
                )

        return ret_grid_scalar_2d

    @classmethod
    def get_grid_vector_2d(
        cls, pb_ret_grid_vector_2d: pb.RetGridVector2D
    ) -> MusicDataBean.RetGridVector2D:
        """
        将protobuf类实例转换为music RetGridVector2D结构数据
        """
        ret_grid_vector_2d = MusicDataBean.RetGridVector2D(
            pb_ret_grid_vector_2d.u_datas,
            pb_ret_grid_vector_2d.v_datas,
            pb_ret_grid_vector_2d.request,
        )
        # 如果该结果数据存在，则将获取的数据，转换为二维数组格式
        if ret_grid_vector_2d:
            ret_grid_vector_2d.request = Utils.set_request_info(
                pb_ret_grid_vector_2d.request
            )
            ret_code = ret_grid_vector_2d.request.error_code
            if ret_code == 0:
                ret_grid_vector_2d.start_lat = pb_ret_grid_vector_2d.startLat
                ret_grid_vector_2d.start_lon = pb_ret_grid_vector_2d.startLon
                ret_grid_vector_2d.end_lat = pb_ret_grid_vector_2d.endLat
                ret_grid_vector_2d.end_lon = pb_ret_grid_vector_2d.endLon
                ret_grid_vector_2d.lat_count = pb_ret_grid_vector_2d.latCount
                ret_grid_vector_2d.lon_count = pb_ret_grid_vector_2d.lonCount
                ret_grid_vector_2d.lon_step = pb_ret_grid_vector_2d.lonStep
                ret_grid_vector_2d.lat_step = pb_ret_grid_vector_2d.latStep
                ret_grid_vector_2d.lats = pb_ret_grid_vector_2d.lats
                ret_grid_vector_2d.lons = pb_ret_grid_vector_2d.lons
                ret_grid_vector_2d.u_ele_name = pb_ret_grid_vector_2d.u_EleName
                ret_grid_vector_2d.v_ele_name = pb_ret_grid_vector_2d.v_EleName
                #                 rows = pbRetGridVector2D.request.rowCount    # 获得数据的行数
                #                 dataLen = len(ret_grid_vector_2d.u_datas)        # 获得所有数据的个数
                #                 cols = dataLen/rows
                rows = ret_grid_vector_2d.lat_count
                cols = ret_grid_vector_2d.lon_count
                ret_grid_vector_2d.u_datas = Utils.set_matrix(
                    rows, cols, ret_grid_vector_2d.u_datas
                )
                ret_grid_vector_2d.v_datas = Utils.set_matrix(
                    rows, cols, ret_grid_vector_2d.v_datas
                )

        return ret_grid_vector_2d

    @classmethod
    def get_ret_files_info(
        cls, pb_ret_files_info: pb.RetFilesInfo
    ) -> MusicDataBean.RetFilesInfo:
        """
        将protobuf类实例转换为music RetFilesInfo结构数据
        """
        ret_files_info = MusicDataBean.RetFilesInfo(pb_ret_files_info.request)
        # 如果该结果数据存在，将获取请求信息，转换为子类对象，进行封装
        if ret_files_info:
            ret_files_info.request = Utils.set_request_info(pb_ret_files_info.request)
            ret_code = ret_files_info.request.error_code
            if ret_code == 0:
                file_infos = pb_ret_files_info.fileInfos
                for i in range(len(file_infos)):
                    ret_files_info.file_infos.append(Utils.set_file_info(file_infos[i]))

        return ret_files_info

    @classmethod
    def set_file_info(cls, pb_file_info: pb.FileInfo) -> MusicDataBean.FileInfo:
        """
        将protobuf类实例转换为music FileInfo结构数据
        """
        file_info = MusicDataBean.FileInfo(
            pb_file_info.fileName,
            pb_file_info.savePath,
            pb_file_info.suffix,
            pb_file_info.size,
            pb_file_info.fileUrl,
            pb_file_info.imgBase64,
            pb_file_info.attributes,
        )

        return file_info
