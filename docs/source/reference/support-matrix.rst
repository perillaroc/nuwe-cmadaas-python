高层 API 代表查询组合
======================

下表只列出当前登记的代表性查询组合、MUSIC interface 和返回类型，不表示在线通过。
组合解析使用精确注册表；未列出的组合不会动态拼接 interface 名称，而会在本地
报告 ``UnsupportedQueryError``。底层 ``CMADaaSClient`` 仍可直接调用其他 MUSIC
interface。
完整逐案登记、实现与真实验证状态将在 D19 从案例清单整合；目前可按
:doc:`高层参考 <high-level>` 的业务指南入口查看具体已验证/待验证边界。

.. list-table::
   :header-rows: 1
   :widths: 24 34 36

   * - 高层入口
     - 查询组合
     - interface / 返回类型
   * - ``retrieve_model_grid``
     - forecast，time + level + valid_time
     - ``getNafpEleGridByTimeAndLevelAndValidtime`` / ``xarray.DataArray``
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
     - time；time_range；element + level_type + time
     - ``getNafpFileByTime``、``getNafpFileByTimeRange``、``getNafpFileByElementAndTime`` / ``list[Path]``
   * - ``retrieve_obs_station``
     - time；time_range + station；time + rect
     - ``getSurfEleByTime`` 等登记接口 / ``pandas.DataFrame``
   * - ``retrieve_obs_grid``
     - time；time + rect
     - ``getSurfEleGridByTime``、``getSurfEleGridInRectByTime`` / ``xarray.DataArray``
   * - ``retrieve_obs_upper_air``
     - time；time + press/height/vertical level；time + station
     - ``getUparEleByTime`` 等登记接口 / ``pandas.DataFrame``
   * - ``download_obs_file``
     - time；time_range；time_range + station
     - ``getSurfFileByTime``、``getSurfFileByTimeRange``、``getSurfFileByTimeRangeAndStaID`` / ``list[Path]``
   * - ``download_obs_upper_air_file``
     - time；time_range；time + station；time_range + station
     - ``getUparFileByTime`` 等四个登记接口 / ``list[Path]``

错误语义
--------

默认模式继续返回 ``MusicError`` 以兼容旧调用；传入 ``strict=True`` 后，服务错误
转换为结构化 ``CMADaaSError``。参数组合未登记、字段类型错误和缺少配对参数属于
本地错误，在网络调用前抛出。
