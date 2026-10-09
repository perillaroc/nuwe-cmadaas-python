观测数据
========

观测入口位于 ``nuwe_cmadaas.obs``，包括三种数据查询和两种文件下载。
下表中的函数名链接完整 API 参考；已存在的教程提供无账号可执行示例。

.. list-table::
   :header-rows: 1

   * - 入口与用途
     - 主要查询参数
     - 结果与教程
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_station`：地面站点
     - ``elements``、``time``、``station``、``region``、``station_level``、``count``
     - ``DataFrame``；:doc:`地面站点 <station>`
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_grid`：地面格点
     - ``parameter``、``time``、``region``
     - ``DataArray``；:doc:`地面格点 <grid>`
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_upper_air`：高空表格
     - ``elements``、``time``、``station``、``region``、``level_type``、``level``、``interface_data_type``
     - ``DataFrame``；:doc:`高空观测 <upper-air>` 展示常规、GPS、Light 和 Ard 分支
   * - :py:func:`~nuwe_cmadaas.obs.download_obs_file`：地面文件
     - ``time``、``station``、``region``、``station_level``、``output_dir``、``count``
     - ``list[Path]``；:doc:`文件下载 <files>`
   * - :py:func:`~nuwe_cmadaas.obs.download_obs_upper_air_file`：高空文件
     - ``time``、``station``、``output_dir``、``count``
     - ``list[Path]``；当前从函数参考查看高空文件包装入口

观测时间与 latest 查询
------------------------------

``time`` 通常使用 ``pandas.Timestamp`` 或标准库 ``datetime`` 表示时次；
支持列表或 ``pandas.Interval`` 的入口可表示多时次或范围，组合仍需已登记。
地面格点当前仅登记时次查询与时次加矩形查询，不能因为签名或类型注解接受时间段
就认定存在对应的范围接口。

地面站点和高空表格的相对 ``Timedelta`` 用于 latest-time 查询，返回时次表格，
字段与普通要素表格不同；该分支只接受资料代码和相对时长，附加筛选会在请求前拒绝。
地面及高空文件下载不接受 latest-time 查询。

表格列保持响应中的字符串；站号、时间、区域和层次筛选必须与所选资料相符。
配置见 :doc:`高层配置 <../../configuration/high-level>`，
同任务的原生参数对照见 :doc:`接口选择 <../../choosing-api>`。
各资料的真实测试日期约定见 :doc:`测试与动态时间 <../../../development/testing>`。

.. toctree::
   :maxdepth: 1

   station
   grid
   upper-air
   files
