示例
====

现有 MUSIC 原生示例位于仓库的 ``example/`` 目录。
地面站点高层示例已位于 ``examples/high_level/station.py``，从仓库根目录运行：

.. code-block:: bash

   uv run python -m examples.high_level.station

脚本默认使用合成数据，无需账号，包含筛选、latest 时次表、数值转换及结果断言。
:doc:`地面站点指南 <../guide/high-level/obs/station>` 复用同一客户端准备和结果校验。

地面格点示例位于 ``examples/high_level/grid.py``，同样从仓库根目录运行：

.. code-block:: bash

   uv run python -m examples.high_level.grid

脚本展示全域和矩形 DataArray 的坐标、数值、名称、单位与元数据，并验证不支持查询
在请求前失败。:doc:`地面格点指南 <../guide/high-level/obs/grid>` 复用准备和结果断言。

高空观测示例位于 ``examples/high_level/upper_air.py``：

.. code-block:: bash

   uv run python -m examples.high_level.upper_air

脚本分别展示常规层次筛选、GPS、雷电、飞机和 latest 表格，断言分支字段与错误零请求。
:doc:`高空观测指南 <../guide/high-level/obs/upper-air>` 复用准备与结果校验，并区分
合成结果和已有在线权限/缺测状态。

地面文件下载示例位于 ``examples/high_level/files.py``：

.. code-block:: bash

   uv run python -m examples.high_level.files

脚本通过公开函数下载四个人工小文件，验证路径、名称、大小与磁盘内容，以及空清单、
严格服务错误和本地拒绝行为；验证后清理临时目录。
:doc:`地面文件指南 <../guide/high-level/obs/files>` 复用准备与结果校验，说明已登记查询、
覆盖行为和真实下载前的清单检查。

完整的高层/MUSIC 示例集及旧包迁移索引将在 D20 整合。
