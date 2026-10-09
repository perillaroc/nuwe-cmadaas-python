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

高空文件下载示例位于 ``examples/high_level/upper_air_files.py``：

.. code-block:: bash

   uv run python -m examples.high_level.upper_air_files

脚本独立调用高空包装函数，覆盖时次、时间段及两种站号组合，实际生成并验证四个文件，
区分空清单、服务错误和本地拒绝，完成后清理临时目录。
:doc:`高空文件指南 <../guide/high-level/obs/upper-air-files>` 展示参数与磁盘结果，
并说明既有在线记录和受控真实服务替换方式。

模式格点示例位于 ``examples/high_level/model_grid.py``：

.. code-block:: bash

   uv run python -m examples.high_level.model_grid

脚本展示预报/分析、全域/矩形、控制/扰动成员等八种登记查询，验证二维坐标、数值、
单位及实际 attrs，并复现本地零请求拒绝和严格服务异常。
:doc:`模式格点指南 <../guide/high-level/model/grid>` 复用准备及结果断言，区分
合成成功、既有在线通过和暂停的按时间查询案例。

模式点示例位于 ``examples/high_level/model_point.py``：

.. code-block:: bash

   uv run python -m examples.high_level.model_point

脚本展示单点、多点、坐标/站号与单时效/范围查询，核对表格字段、原始字符串与 attrs，
并在副本上显式转换数值和有效时间；空表格、严格服务异常及本地零请求错误分别验证。
:doc:`模式点指南 <../guide/high-level/model/point>` 复用准备和断言，说明坐标顺序、
范围元数据边界及动态日期的真实服务替换。

模式文件示例位于 ``examples/high_level/model_files.py``：

.. code-block:: bash

   uv run python -m examples.high_level.model_files

脚本通过七种模式文件组合及普通时效过滤生成八个小文件，检查路径、大小、内容并清理；
latest 单独查询 Datetime 表格，空清单、严格服务异常和本地请求前拒绝分别验证。
:doc:`模式文件指南 <../guide/high-level/model/files>` 说明要素/层次、count 限制、
data_type 当前行为及真实下载前的清单规模检查。

底层表格示例位于 ``examples/music/tables.py``：

.. code-block:: bash

   uv run python -m examples.music.tables

脚本通过真实 MUSIC 客户端和人工 protobuf 验证原生参数、Array2D 的 request/ok、
列名、字符串数组与 DataFrame 的 dtype/attrs，以及副本上的显式数值转换。
成功空结果、服务错误和解码错误分别验证，失败转换抛异常，四次响应均关闭。
:doc:`底层表格指南 <../guide/low-level/tables>` 复用同一准备工厂和独立断言，
提供只供手动执行的真实服务替换。

底层格点示例位于 ``examples/music/grids.py``：

.. code-block:: bash

   uv run python -m examples.music.grids

脚本分别调用 gridArray2D、gridScalar2D 和 gridVector2D，核对原生参数、原始数组、
2×3 坐标、数值、名称、单位及完整 attrs；两个方法返回 DataArray，矢量返回 U/V Dataset。
三种空场和服务失败及一条坏矢量验证成功/错误边界，十次响应均关闭。
:doc:`底层格点指南 <../guide/low-level/grids>` 复用同一准备和独立断言，保留
三个既有在线案例锚点，说明矢量单位和 GFS 预报/分析的真实替换边界。

底层文件示例位于 ``examples/music/files.py``：

.. code-block:: bash

   uv run python -m examples.music.files

脚本分别执行 metadata-only 的 fileList 和实际流式写入的 downFile，核对 FilesInfo、
FileInfo 字段与磁盘大小/内容，展示已有目标拒绝、默认覆盖和批量部分完成；
成功空清单、服务失败、响应关闭和临时目录清理分别验证。
:doc:`文件清单指南 <../guide/low-level/file-list>` 与
:doc:`文件下载指南 <../guide/low-level/downloads>` 独立复用准备和对应断言，
保留 LLF 案例锚点，真实替换采用 GFS 动态日期及下载规模预查。

底层格式化输出示例位于 ``examples/music/serialization.py``：

.. code-block:: bash

   uv run python -m examples.music.serialization

脚本实际执行 JSON/XML/text/HTML 四种格式的字符串请求和文件保存，解析结构并
核对实际磁盘正文，验证 dataFormat 保留、savepath 改写、目标覆盖和临时目录清理。
兼容错误文本、原始业务错误、无效 UTF-8 和保存的服务/网关/解码错误分别展示，
None 目标和成功空保存清单的现有行为单独验证。
:doc:`序列化指南 <../guide/low-level/serialization>` 与
:doc:`格式化保存指南 <../guide/low-level/save-as-file>` 各自复用准备和断言，
保留八个 LLR/LLS 案例锚点和已有在线通过，真实替换不在构建中执行。

完整的高层/MUSIC 示例集及旧包迁移索引将在 D20 整合。
