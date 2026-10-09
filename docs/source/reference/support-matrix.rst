高层 API 支持矩阵
=================

下表列出高层 API 当前承诺的代表性查询组合、登记的 MUSIC interface 和返回类型。
组合解析使用精确注册表；未列出的组合不会动态拼接 interface 名称，而会在本地
报告 ``UnsupportedQueryError``。底层 ``CMADaaSClient`` 仍可直接调用其他 MUSIC
interface。

.. list-table::
   :header-rows: 1
   :widths: 24 34 36

   * - 高层入口
     - 查询组合
     - interface / 返回类型
   * - ``retrieve_model_grid``
     - forecast，无时间/层次/区域条件
     - ``getNafpEleGrid`` / ``xarray.DataArray``
   * - ``retrieve_model_grid``
     - time + level + valid_time + rect + member
     - ``getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember`` / ``xarray.DataArray``
   * - ``retrieve_model_point``
     - time + level + valid_time + point
     - ``getNafpEleAtPointByTimeAndLevelAndValidtime`` / ``pandas.DataFrame``
   * - ``retrieve_model_point``
     - time + level + valid_time_range + station
     - ``getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID`` / ``pandas.DataFrame``
   * - ``download_model_file``
     - no filter；element + time；time_range + level
     - ``getNafpFile``、``getNafpFileByElementAndTime``、``getNafpFileByTimeRangeAndLevel`` / ``list[Path]``
   * - ``retrieve_obs_station``
     - time；time_range + station；rect/region/basin
     - ``getSurfEleByTime`` 等登记接口 / ``pandas.DataFrame``
   * - ``retrieve_obs_grid``
     - time；time_range + rect
     - ``getSurfEleGridByTime``、``getSurfEleGridInRectByTimeRange`` / ``xarray.DataArray``
   * - ``retrieve_obs_upper_air``
     - time；time + press/height/vertical level；station
     - ``getUparEleByTime`` 等登记接口 / ``pandas.DataFrame``
   * - ``download_obs_file``
     - time；station；station_range；region
     - ``getSurfFile...`` 登记接口 / ``list[Path]``
   * - ``download_obs_upper_air_file``
     - time；station；station_range
     - ``getUparFile...`` 登记接口 / ``list[Path]``

错误语义
--------

默认模式继续返回 ``MusicError`` 以兼容旧调用；传入 ``strict=True`` 后，服务错误
转换为结构化 ``CMADaaSError``。参数组合未登记、字段类型错误和缺少配对参数属于
本地错误，在网络调用前抛出。
