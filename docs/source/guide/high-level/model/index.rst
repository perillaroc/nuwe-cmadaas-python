模式数据
========

模式入口位于 ``nuwe_cmadaas.model``，按格点、点／站点和文件组织。
下表的函数名链接完整 API 参考；三个模式入口均有独立可执行指南。

.. list-table::
   :header-rows: 1

   * - 入口与用途
     - 主要查询参数
     - 成功返回值
   * - :py:func:`~nuwe_cmadaas.model.retrieve_model_grid`：预报或分析二维格点
     - ``parameter``、``start_time``、``forecast_time``、``level_type``、``level``、``region``、``number``、``data_type``
     - ``xarray.DataArray``；:doc:`模式格点 <grid>` 展示预报、分析、区域和成员
   * - :py:func:`~nuwe_cmadaas.model.retrieve_model_point`：经纬度点或站点预报
     - ``parameter``、``start_time``、``forecast_time``、``level_type``、``level``、``point`` 或 ``station``
     - ``pandas.DataFrame``；:doc:`模式点与站点 <point>` 展示坐标/站号与单时效/范围
   * - :py:func:`~nuwe_cmadaas.model.download_model_file`：模式产品文件
     - ``parameter``、``start_time``、``forecast_time``、``level_type``、``level``、``region``、``output_dir``、``count``
     - ``list[Path]``；:doc:`模式文件 <files>` 展示筛选、下载规模及 latest 表格边界

起报时间与时效
--------------

公开参数是 ``start_time`` 和 ``forecast_time``；不要将内部 feature 名 ``time``、
``valid_time`` 或 ``valid_time_range`` 直接传给模式函数。
单时效可使用 ``pandas.Timedelta``、标准库 ``timedelta`` 或如 ``"24h"`` 的字符串。
模式点入口另支持两个时效组成的元组作为范围；不要将这个范围能力推广到格点或文件入口。

模式格点的 ``data_type`` 区分 ``forecast`` 和 ``analysis``，具体组合依赖登记和资料；
集合成员使用 ``number``。层次由 ``level_type`` 与 ``level`` 配对提供。
二维格点结果不自动增加多时效、多层次或多成员维度；已有请求信息放在 ``attrs`` 中。

点与文件的边界
--------------

``point`` 按 ``(纬度, 经度)`` 顺序传坐标对，也可传多个坐标对的列表。
模式点中的 ``point`` 和 ``station`` 互斥；站点范围不属于此入口支持的站点类型。
文件函数下载到 ``output_dir`` 并返回实际路径，latest-time 查询不作为文件下载。

资料代码、要素、层次与时效必须按对应接口核对，不能以同属一个模式就推断全部组合可用。
成功表格保留字符串值，格点坐标使用 ``latitude/longitude``；错误语义见
:doc:`高层接口概览 <../index>`。配置与动态日期分别见
:doc:`高层配置 <../../configuration/high-level>` 和
:doc:`测试与动态时间 <../../../development/testing>`。

.. toctree::
   :maxdepth: 1

   grid
   point
   files
