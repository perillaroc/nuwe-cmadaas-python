示例
====

统一示例位于仓库的 ``examples/`` 目录，完整源码和运行说明可
:download:`下载统一 README <../../../examples/README.md>`。
安装主项目后从仓库根目录运行，不需要第二个发行包或 Click：

.. code-block:: bash

   uv sync
   uv run python -m examples --list
   uv run python -m examples station
   uv run python -m examples --all

统一入口复用下列现有脚本及其断言，默认全部为人工数据；临时输出验证后清理。
指南和脚本继续共享准备与校验，公开调用留在教学代码中。原生独特场景见本页末尾，
旧包仍作为兼容过渡保留，不用于默认离线执行。
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

底层数据块示例位于 ``examples/music/data_block.py``：

.. code-block:: bash

   uv run python -m examples.music.data_block

脚本经真实客户端解码人工 RetDataBlock，核对名称、原始 bytes、BytesIO/struct
读取、状态/metadata、参数未修改和能力警告；空成功、含内容的服务失败、解码失败及
文本/表格/格点转换边界分别验证。四次响应关闭，不写文件，临时目录清理。
:doc:`数据块指南 <../guide/low-level/data-block>` 复用准备和独立断言，
保留 LLB-001 待确认及默认关闭状态，真实替换代码在确认接口/资料/样本后才可请求。

全部八个高层入口和九个底层方法可按上述模块独立运行，也可从统一入口选择。

通用 :doc:`结果指南 <../guide/results>` 与 :doc:`错误指南 <../guide/errors>`
复用 ``examples/high_level/handling.py`` 中的精确客户端工厂和独立断言。
该模块作为页面辅助代码使用，教学调用直接保留在两页的可执行单元中；
严格文档构建会验证数值/缺测/单位/attrs、空表/空场/空路径、实际文件，
以及 MusicError/strict、错误上下文、转换错误和参数/配置请求前拒绝。

旧原生场景与兼容迁移
--------------------

``examples/music/scenarios.py`` 保留站点统计 ``statSurfEle``、站点元数据
``getStaInfoInRect``、雷达文件 ``getRadaFileByTimeRangeAndStaId``、模式点时序和
U/V 矢量格点等原生场景。JSON/XML/text/HTML 变体合并为参数：

.. code-block:: bash

   uv run python -m examples.music.scenarios station_statistics
   uv run python -m examples.music.scenarios station_info --operation serialized --format xml
   uv run python -m examples.music.scenarios radar_files --operation download
   uv run python -m examples --legacy music/grid_element_rect_search/grid_element_rect_search_grid_verctor_2d.py

新场景保持原生 interface、字段/统计要素、层次/时效、站点/矩形条件；
历史非日期参数保存在 ``examples/legacy-migration.json``，实际运行替换为虚构资料与
小规模响应。原数组脚本文件名带 rect 却使用全域 ID，另有矩形格式化入口；
通用格点的地面层/零时效、十五列站点时间段查询也分别保留。
这些原生示例不新增高层注册键，也不更新 :doc:`支持矩阵 <../reference/support-matrix>`
的在线记录。旧包独特能力的真实服务验证仍须确认资料、权限和返回形式。

逐项去向可 :download:`下载旧路径迁移索引 <../../../example/MIGRATION.md>`；
58 条记录由 JSON 生成，更新后运行 ``python -m examples --write-migration-index``。
``--legacy`` 执行原场景对应的离线替代，旧 Click 认证/输出选项不传给新入口。
原 ``example/`` 中的脚本、导入路径、空占位和打包配置保留兼容过渡，说明见
:download:`旧包 README <../../../example/README.md>`。本地未见下游引用不能判断外部
安装用户；至少保留至本轮迁移及 E06 验收完成，外部依赖核查/通知和退出条件仍须
单独满足，不能据离线通过直接删除独立包。

新 CLI 不读取真实配置。手动真实调用使用显式客户端注入，
``examples/_support/live_config.py`` 只读取明确的 CedarKit YAML 路径，
``make_live_params()`` 要求原生资料/字段/筛选并按运行日期生成时次；不沿用人工
配置或固定日期。INI 模板可 :download:`下载 <../../../examples/config/client.config.example>`，
认证另传 user/password。实际保存/下载须显式给输出路径并自行检查规模，完整示例
见统一 README，配置语义见 :doc:`底层配置 <../guide/configuration/music-client>`。

.. code-block:: bash

   uv sync --group test --group docs
   uv run pytest tests/unit/test_examples.py tests/unit/test_example_support.py --disable-socket --strict-markers -q

默认离线示例、原生替代和旧 CLI 的 help 可在禁用 socket 的环境验证；真实服务
片段不在这类检查中执行。修改入口或原生场景时，先更新 ``examples/catalog.py``
或 ``examples/music/scenarios.py``，保持脚本断言与指南中的可见调用一致；旧路径映射
改动还须更新 ``examples/legacy-migration.json``，运行
``python -m examples --write-migration-index`` 重新生成索引。然后运行上面的离线测试、
``uv run python -m examples --all`` 和 :doc:`严格文档构建 <documentation>`。
合成成功不更新在线案例状态；真实服务结果按 :doc:`测试说明 <testing>` 逐案记录。
