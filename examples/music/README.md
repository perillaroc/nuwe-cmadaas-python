# MUSIC 原生示例

从完整源码仓库根目录运行；仅安装 wheel 不包含这些辅助模块。
脚本使用 `examples/_support/` 的人工 protobuf 和精确 `SyntheticTransport`，
注入真实 `CMADaaSClient`，无需配置或账号。未知请求立即失败，不回退真实网络。

```bash
uv run python -m examples.music.tables
```

`tables.py` 展示原生 interface/params、Array2D 的 request/ok、列名与字符串数组、
`to_pandas()`、实际 dtype/attrs 及副本上的显式数值转换；成功空结果、服务错误和
解码错误分别验证，失败转换抛结构化异常。四次响应均核对关闭状态。
指南 `docs/source/guide/low-level/tables.md` 复用同一客户端工厂与独立结果断言。
真实服务替换仅作为手动代码展示，不在脚本或文档构建中执行。

```bash
uv run python -m examples.music.grids
```

`grids.py` 分别执行 gridArray2D、gridScalar2D 和 gridVector2D，核对原生参数、
request/ok、2×3 坐标/数值、名称、单位及实际 attrs，区分两个 DataArray 与 U/V Dataset。
三种成功空场、三种服务错误和坏矢量的解码错误分别验证，十次响应均关闭。
指南 `docs/source/guide/low-level/grids.md` 复用同一准备和独立结果断言，真实替换
采用已有 GFS 预报/分析组合；风分量单位不会由转换自动补齐。

```bash
uv run python -m examples.music.files
```

`files.py` 分别运行元数据查询和真实流式下载。清单部分核对三个 FilesInfo 及 FileInfo
字段，并证明没有正文请求或磁盘写入；下载部分实际写入 first.bin/second.bin，
验证已有目标拒绝、默认覆盖、批量部分写入、空清单/服务失败与全部响应关闭。
所有输出目录临时创建，验证后清理。指南 `docs/source/guide/low-level/file-list.md`
和 `downloads.md` 分别复用准备与对应断言；返回仍是 FilesInfo，不是 list[Path]。

```bash
uv run python -m examples.music.serialization
```

`serialization.py` 实际执行四种格式的 serializedStr 和 saveAsFile，核对原始字符串、
JSON/XML/text/HTML 结构与实际磁盘内容、参数修改和目标覆盖，完成后清理临时目录。
字符串错误兼容文本、原始业务错误、无效 UTF-8，以及保存的服务/网关/解码失败、
None 目标和成功空清单的现有 IndexError 分别验证；未知请求不回退网络。
指南 `docs/source/guide/low-level/serialization.md` 与 `save-as-file.md` 独立复用准备
与断言，保留八个 LLR/LLS 案例锚点，真实替换仅作手动代码展示。

```bash
uv run python -m examples.music.data_block
```

`data_block.py` 用虚构接口经真实客户端解码 RetDataBlock，核对名称、十个非文本字节、
BytesIO/struct 读取结果、request/metadata、参数保留和每次调用的能力警告。
空成功、含 bytes 的服务失败、坏 protobuf、文本解码与未实现的转换分别验证，
四次响应全部关闭，不写文件，临时空目录清理。指南
`docs/source/guide/low-level/data-block.md` 复用准备与断言，保留 LLB-001 待确认/默认关闭
边界；真实替换要求先确认 RetDataBlock 接口、资料、近期受控样本和内容格式。

统一入口、全部公开方法与旧场景迁移见 [examples/README.md](../README.md)。
