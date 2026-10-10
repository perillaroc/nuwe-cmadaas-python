# 仓库示例集

取得完整源码，在**仓库根目录**使用 Python 3.11+ 安装主项目，再运行示例：

```bash
uv sync
uv run python -m examples --list
uv run python -m examples station
uv run python -m examples --all
```

已有 Python 环境也可用 `python -m pip install .` 后执行 `python -m examples ...`。
`examples/` 是源码仓库内的示例集，wheel 不包含它；不需要安装第二个发行包，
新入口只用标准库 CLI，不需要 Click。`--all` 验证下表全部入口及原生场景，
单个模块的原运行方式仍保留，可用来查看完整教学输出。

默认全部使用明确标注的人工 protobuf、字符串和小文件，注入真实 MUSIC 客户端，
实际执行解码、转换和流式写文件；未知请求立即失败。固定日期、虚构资料/站号、
统计值、单位和序列化 schema 只用于教学，不证明真实服务能力。下载/保存使用临时
目录，核对内容与大小后清理；不会读取账号、用户配置或访问真实服务。
模拟机制见 [模拟数据与客户端注入](../docs/source/guide/simulated-data.md)。

## 高层入口

新使用者可先按任务选择高层示例，无需先学习 MUSIC interface ID。

| `python -m examples` 后的名称 | 公开函数 | 共享脚本与指南 |
| --- | --- | --- |
| `station` | `retrieve_obs_station` | [station.py](high_level/station.py) · [站点指南](../docs/source/guide/high-level/obs/station.md) |
| `obs-grid` | `retrieve_obs_grid` | [grid.py](high_level/grid.py) · [地面格点](../docs/source/guide/high-level/obs/grid.md) |
| `upper-air` | `retrieve_obs_upper_air` | [upper_air.py](high_level/upper_air.py) · [高空观测](../docs/source/guide/high-level/obs/upper-air.md) |
| `obs-files` | `download_obs_file` | [files.py](high_level/files.py) · [地面文件](../docs/source/guide/high-level/obs/files.md) |
| `upper-air-files` | `download_obs_upper_air_file` | [upper_air_files.py](high_level/upper_air_files.py) · [高空文件](../docs/source/guide/high-level/obs/upper-air-files.md) |
| `model-grid` | `retrieve_model_grid` | [model_grid.py](high_level/model_grid.py) · [模式格点](../docs/source/guide/high-level/model/grid.md) |
| `model-point` | `retrieve_model_point` | [model_point.py](high_level/model_point.py) · [模式点](../docs/source/guide/high-level/model/point.md) |
| `model-files` | `download_model_file` | [model_files.py](high_level/model_files.py) · [模式文件](../docs/source/guide/high-level/model/files.md) |

完整模块运行说明见 [high_level/README.md](high_level/README.md)。通用结果与错误页面
复用 `high_level/handling.py` 的工厂/断言，该辅助模块不设重复 CLI。

## 底层九个方法

| 入口名称 | `CMADaaSClient` 方法 | 共享脚本与指南 |
| --- | --- | --- |
| `tables` | `callAPI_to_array2D` | [tables.py](music/tables.py) · [表格](../docs/source/guide/low-level/tables.md) |
| `grids` | `callAPI_to_gridArray2D` | [grids.py](music/grids.py) · [格点](../docs/source/guide/low-level/grids.md) |
| `grids` | `callAPI_to_gridScalar2D` | 同上，单独验证标量响应 |
| `grids` | `callAPI_to_gridVector2D` | 同上，单独验证 U/V Dataset |
| `file-list` | `callAPI_to_fileList` | [files.py](music/files.py) · [文件清单](../docs/source/guide/low-level/file-list.md) |
| `downloads` | `callAPI_to_downFile` | [files.py](music/files.py) · [实际下载](../docs/source/guide/low-level/downloads.md) |
| `serialization` | `callAPI_to_serializedStr` | [serialization.py](music/serialization.py) · [序列化](../docs/source/guide/low-level/serialization.md) |
| `save-as-file` | `callAPI_to_saveAsFile` | [serialization.py](music/serialization.py) · [格式化保存](../docs/source/guide/low-level/save-as-file.md) |
| `data-block` | `callAPI_to_dataBlock` | [data_block.py](music/data_block.py) · [数据块](../docs/source/guide/low-level/data-block.md) |

两种格式方法均验证 JSON/XML/text/HTML。DataBlock 保留能力警告和在线未验证边界。
返回类型、空结果、错误与已有目标处理见 [music/README.md](music/README.md) 及对应指南。

## 旧场景的原生替代

[music/scenarios.py](music/scenarios.py) 合并旧场景和格式变体。先运行：

```bash
uv run python -m examples.music.scenarios --help
uv run python -m examples.music.scenarios station_statistics
uv run python -m examples.music.scenarios station_info --operation serialized --format xml
uv run python -m examples.music.scenarios model_point --operation save --format json
uv run python -m examples.music.scenarios radar_files --operation download
uv run python -m examples --legacy music/station_element_statistics/station_element_statistics_array_2d.py
```

| 场景 | 实际保留的原生 interface / 特征 |
| --- | --- |
| `station` | `getSurfEleByTime`，原八列要素、排序与数量 |
| `station_range` | `getSurfEleByTimeRange`，原十五列要素与两小时窗口 |
| `station_statistics` | `statSurfEle`，`statEles` 的四种统计字段、六小时闭区间、`orderBy` 原拼写；新示例统一限制十行 |
| `station_info` | `getStaInfoInRect`，站点元数据、经纬度/海拔与矩形 |
| `model_point` | `getNafpEleAtPointByTimeAndLevelAndValidtimeRange`，两个坐标与 0～12 小时时效 |
| `model_grid` | `getNafpEleGridByTimeAndLevelAndValidtime`，850 hPa、24 小时 |
| `model_grid_surface` | 同一 ID，旧通用格点的 `levelType=1/fcstLevel=0/validTime=0` |
| `model_grid_rect` | `getNafpEleGridInRectByTimeAndLevelAndValidtime`，矩形格式化查询 |
| `vector_grid` | `getNafpVectorEleGridByTimeAndLevelAndValidtime`，`fcstuele/fcstvele` 和真实 U/V 转换 |
| `radar_files` | `getRadaFileByTimeRangeAndStaId`，多个雷达站与一小时窗口；清单和正文下载分开 |
| `model_files` | `getNafpFileByTime`，清单和下载 |

默认 `--operation query` 使用场景原有响应方法；`serialized` 与 `save` 用
`--format {json,xml,text,html}`，文件场景还可用 `download`。矢量场景只保留其原有
gridVector2D 用法。`save` 返回 FilesInfo 并验证实际文件，`serialized` 返回 str；
表格/格点实际转换，原始字段与字符串数值保留，不自动改单位或缺测。

统计、站点信息、雷达和矩形格式化查询都属于底层用法，不能据此添加或推断高层
注册组合。特别是旧文件名带 rect 的数组脚本实际调用全域 ID；迁移保留该事实。
[完整支持矩阵](../docs/source/reference/support-matrix.rst) 区分登记、实现和历史在线状态，
这些新场景没有新增在线通过记录。

## 显式切换真实服务

新 CLI 保持离线。需手动确认 interface、资料权限、字段、原生参数、返回形式与近期
样本，再注入真实客户端。高层请使用相应指南的 `config=` 或 `client=` 示例。
原生只查询的小例子如下，**需真实服务，不会在离线验证或文档构建中执行**：

```python
from examples._support.live_config import make_live_music_client
from examples.music.scenarios import make_live_params, query

params = make_live_params("station_info", {
    "dataCode": "YOUR_AUTHORIZED_STATION_INFO_CODE",
    "elements": "YOUR_VERIFIED_FIELDS",
    "minLat": "39", "maxLat": "42", "minLon": "115", "maxLon": "117",
})
client = make_live_music_client("/path/to/cedarkit.yaml")
response = query(client, "station_info", params)
print(response.to_pandas())
```

先替换全部占位值；缺少原生参数或保留虚构值会在读取账号前拒绝。
`make_live_params()` 要求调用者显式提供资料、字段及筛选，不沿用人工默认值；
地面查询采用运行日期前一天 00 时、模式查询三天前 06 时。雷达采用底层 MUSIC
三天前 06 时约定，仍须自行核实资料的可用窗口；站点信息没有日期条件。
原生字典不可直接带固定 `time/times/timeRange`，由辅助函数生成运行时日期。
此处的默认时段仅为示例约定，实际能力与参数拼写应以服务确认结果为准。

`make_live_music_client()` 只读取显式给定的 CedarKit YAML，构造时不发请求，采用
summary 日志；它属于示例辅助代码。底层 INI 示例见
[config/client.config.example](config/client.config.example)，认证需另传 `user/password`。
YAML、INI、构造选项与生命周期见 [配置指南](../docs/source/guide/configuration/music-client.md)。
客户端注入时调用者负责生命周期；真实下载/保存还须预查询规模、显式输出目录并
按 [集成测试说明](../tests/integration/README.md) 设置数量/字节上限，库方法本身没有
本地总量限制。`query()` 的 protobuf 响应显式检查错误；序列化 str 沿用原始正文语义，
须另核对业务状态，不能仅凭字符串存在计为成功。

## 兼容过渡

[58 条旧脚本逐项迁移索引](../example/MIGRATION.md) 从
[legacy-migration.json](legacy-migration.json) 生成，保留实际 interface、方法、格式和
历史非日期参数。更新 JSON 后运行 `python -m examples --write-migration-index`。
`--legacy` 接受旧相对路径或 `example/nuwe_cmadaas_example/` 前缀，执行离线替代，
不解释旧 Click 的认证/输出选项。

原 `example/nuwe_cmadaas_example.*` 导入与脚本路径、辅助函数、INI 示意和
`example/pyproject.toml` 保留兼容过渡；原脚本仍依赖 Click，运行会访问服务，且旧日期/
资料不能直接视为当前可用。旧空高层占位的使用去向为 `model-grid`。
过渡安装方式及退出条件见 [example/README.md](../example/README.md)。本地未见下游
引用不能证明没有外部安装用户；退出前须完成替代验证、外部依赖核查与迁移通知。
