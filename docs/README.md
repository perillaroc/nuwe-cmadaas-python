# 文档构建

开发流程与维护约定见 `docs/source/development/documentation.rst`；
测试命令见 `docs/source/development/testing.md`，示例维护见
`docs/source/development/examples.rst`。

在仓库根目录使用 Python 3.11 或更新版本：

```bash
uv sync --group docs
uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html
```

RST 页面用于 API 参考，MyST-NB Markdown 页面用于可执行教程。配置对 Notebook 使用
`nb_execution_mode = "force"`；构建时需要允许 Jupyter 内核通过本机 socket 通信。
无账号快速入门、两层接口对照、全部八个高层入口及九个底层方法已有可执行教程。
序列化与格式化保存展示四种格式；数据块展示名称、bytes 与读取方式，其真实服务能力仍待确认。
`guide/results.md` 和 `guide/errors.md` 独立执行数值/缺测/单位/attrs、空结果、
默认 MusicError/strict、底层错误上下文和本地参数/配置错误的处理示例。
`reference/` 已收录八个高层入口、客户端九个方法、响应对象、配置类型/辅助函数、
异常与兼容契约；`reference/support-matrix.rst` 从案例清单生成完整逐案矩阵。
矩阵区分精确登记、测试实现与历史在线验证，每条案例均关联测试源码和指南锚点。
构建时检查当前注册键覆盖并重新计算汇总；无需手工维护第二份状态表。

## 可执行模拟页面

复制 `docs/templates/executable-page.md` 到 `docs/source/` 下的目标章节，并在
`docs/simulated-pages.json` 的 `pages` 中登记相对 `docs/` 的路径。模板的
`simulated_data: true` 标记、Python kernel、专章链接和代码单元顺序是页面约定。
登记后运行 `python3 docs/check_simulated_pages.py`，检查页面、专章链接和折叠标签。

每页都从本仓库的 `examples/_support/` 导入辅助代码。Notebook 从工作目录向上
查找仓库；若在独立的临时文档树执行，设置 `NUWE_CMADAAS_REPO_ROOT` 为此仓库
根目录。读者应取得完整源码仓库，安装项目的文档依赖，再运行示例；仅安装
`nuwe_cmadaas` wheel 不包含这些辅助代码。

准备和注入步骤放在首个 `hide-input` 单元中，生成的 HTML 应可展开该单元。
公开 API 的导入、实际调用和结果表达式留在普通代码单元中。只供构建校验的
断言可单独用 `remove-cell`；业务错误处理仍要直接展示。每页单独准备客户端，
不得依赖别的页面执行顺序。所有模拟页面须在首个代码单元前，用可见的
`{doc}` 交叉引用链接到“模拟数据与客户端注入”专章。

高层教程在准备单元中用 `FakeClient.register()` 登记精确请求，或使用注入
`SyntheticTransport` 的真实 MUSIC 客户端；调用单元保留公开函数的 `client=client`。
地面站点指南复用 `examples/high_level/station.py` 的客户端准备及结果断言，
从仓库根目录可用 `uv run python -m examples.high_level.station` 独立运行。
地面格点指南同样复用 `examples/high_level/grid.py`，以
`uv run python -m examples.high_level.grid` 独立运行全域和矩形查询及结果断言。
高空指南复用 `examples/high_level/upper_air.py`；
`uv run python -m examples.high_level.upper_air` 独立运行常规、GPS、Light、Ard 和 latest 示例。
地面文件指南复用 `examples/high_level/files.py`；
`uv run python -m examples.high_level.files` 将四个小文件下载到临时目录，验证并自动清理。
高空文件指南复用 `examples/high_level/upper_air_files.py`；
`uv run python -m examples.high_level.upper_air_files` 独立验证四种高空下载组合及实际文件清理。
模式格点指南复用 `examples/high_level/model_grid.py`；
`uv run python -m examples.high_level.model_grid` 独立验证八种预报/分析查询的数组、坐标和元数据。
模式点指南复用 `examples/high_level/model_point.py`；
`uv run python -m examples.high_level.model_point` 独立验证坐标/站号的单时效和范围表格及显式转换。
模式文件指南复用 `examples/high_level/model_files.py`；
`uv run python -m examples.high_level.model_files` 下载并清理八个小文件，另验证 latest 表格与错误边界。
底层表格指南复用 `examples/music/tables.py`；
`uv run python -m examples.music.tables` 独立验证原生参数、request/ok、字符串数组、
DataFrame 和显式数值转换，以及成功空结果、服务/解码错误和响应关闭。
底层格点指南复用 `examples/music/grids.py`；
`uv run python -m examples.music.grids` 独立验证三种格点响应、坐标/数值/单位、
DataArray 与 U/V Dataset 的实际 attrs、空场、服务失败及坏矢量的解码失败。
底层文件清单和下载指南复用 `examples/music/files.py`；
`uv run python -m examples.music.files` 分别验证只查询元数据和实际流式下载，
核对 FilesInfo/磁盘内容、默认覆盖、已有目标拒绝、批量部分完成及临时目录清理。
底层序列化与格式化保存复用 `examples/music/serialization.py`；
`uv run python -m examples.music.serialization` 验证 JSON/XML/text/HTML 字符串及
实际保存文件、dataFormat/savepath 修改、兼容错误和异常边界，并清理临时目录。
底层教程在准备单元中登记 `SyntheticTransport`
的请求和下载 URL，并调用 `make_synthetic_music_client(transport)`；调用单元
直接展示对应的 `callAPI_to_*` 方法及结果。下载页在页面内创建临时目录并
展示相对文件名及大小，不展示随机的绝对路径。

`docs/requirements.txt` 与 `pyproject.toml` 的 `docs` 依赖组保持相同的直接依赖。
Read the Docs 按 `.readthedocs.yml` 先安装前者，再安装本项目；该配置仍请求 PDF。
具备 TeX 工具链时，可先构建 LaTeX 源文件，再检查 PDF 输出：

```bash
uv run --group docs sphinx-build -b latex -E -a -W --keep-going docs/source docs/build/latex
make -C docs/build/latex all-pdf
```

PDF 的实际渲染验收属于 E05；后续文档与示例的 CI 检查属于 D22。
