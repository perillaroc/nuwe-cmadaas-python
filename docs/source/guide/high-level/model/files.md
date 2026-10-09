---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 模式文件下载

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.model.download_model_file` 下载模式产品文件。
成功返回 `list[pathlib.Path]`，每个 Path 指向实际下载的本地文件；它不是格点
DataArray、点预报 DataFrame 或底层 FilesInfo 清单。

`data_code` 选择资料，`start_time` 选择起报时次或起报时间段；可选字符串 `parameter`
选择要素文件，并要求 `level_type`，具体 `level` 可以省略。
`forecast_time` 是单一预报时效，`output_dir` 是本地目录。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_MODEL_FILES`、`synthetic_temperature`、固定起报 `2026-01-02 06:00` 和
`.invalid` 地址只用于离线演示。文件内容是人工 bytes，不代表真实 GRIB 或其他格式。

本页注入合成 transport 的真实 MUSIC 客户端，经 protobuf 解码清单，再流式写入
临时目录。准备阶段不预写文件，不替换高层函数；未知请求/URL 立即失败，不回退网络。
输出只展示相对名称、实际大小和小文件内容，最后明确清理。

```{code-cell} ipython3
:tags: [hide-input]

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

start = Path(os.environ.get("NUWE_CMADAAS_REPO_ROOT", Path.cwd())).resolve()
repo_root = next(
    (path for path in (start, *start.parents)
     if (path / "examples" / "_support" / "synthetic.py").is_file()),
    None,
)
if repo_root is None:
    raise RuntimeError("Run this example from a nuwe-cmadaas-python checkout")
sys.path.insert(0, str(repo_root))

from examples.high_level.model_files import make_model_file_client, check_results

client, transport = make_model_file_client()
directory = TemporaryDirectory()
output_root = Path(directory.name)
```

(mf-003)=
## 按起报时次下载

不指定要素或层次时选择普通时次文件接口；`count=1` 请求最多一条清单记录。
它不限制单个文件大小，真实下载前还需预查字节数。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.model import download_model_file

cycle = pd.Timestamp("2026-01-02 06:00")
single_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", start_time=cycle, count=1,
    output_dir=output_root / "single", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in single_paths]
```

选择 `getNafpFileByTime`，`time="20260102060000"`、`limitCnt="1"`，
实际下载 `single/time.bin`，大小 4 字节，内容 `b"TIME"`。

```{code-cell} ipython3
{
    "返回列表": isinstance(single_paths, list),
    "元素为 Path": all(isinstance(path, Path) for path in single_paths),
    "文件存在": all(path.is_file() for path in single_paths),
}
```

(mf-004)=
## 按起报时间段下载

`pd.Interval` 指定起报时间范围及端点闭合方式，这与预报时效范围不同。
本例使用一小时左闭右开区间，仍限定最多一条清单记录：

```{code-cell} ipython3
window = pd.Interval(cycle, cycle + pd.Timedelta(hours=1), closed="left")
range_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", start_time=window, count=1,
    output_dir=output_root / "range", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in range_paths]
```

选择 `getNafpFileByTimeRange`，时间段为 `[20260102060000,20260102070000)`，
实际下载 `range/range.bin`，大小 5 字节。清单决定文件数，不由区间长度推断。

(mf-008)=
## 要素与层次类型：可以省略具体层次

字符串 `parameter` 生成 `fcstEle` 并选择要素接口。五个要素接口都要求 `levelType`，
但只有包含具体层次的组合要求 `fcstLevel`；下面只给层次类型 103，不给 level。
**要素接口不能传 count**，调用前应按清单检查文件数量和大小。

```{code-cell} ipython3
element_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", parameter="synthetic_temperature", level_type=103,
    start_time=cycle, output_dir=output_root / "element", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in element_paths]
```

选择 `getNafpFileByElementAndTime`，实际下载 `element/element.bin`，大小 7 字节。
不指定具体层次不表示文件只含 2 米层次，也不保证文件很小。

(mf-009)=
### 要素加起报时间段

```{code-cell} ipython3
element_range_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", parameter="synthetic_temperature", level_type=103,
    start_time=window, output_dir=output_root / "element_range", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in element_range_paths]
```

选择 `getNafpFileByElementAndTimeRange`，实际生成 `element_range/element-range.bin`，
大小 13 字节。当前此时间段组合不支持再加具体 level 或 forecast_time。

(mf-010)=
## 要素加具体层次

指定 `level=2` 须同时有 `level_type=103`，按服务层次约定表示 2 米高度。
参数限制的是请求条件，文件组织和内容仍以资料定义为准。

```{code-cell} ipython3
level_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", parameter="synthetic_temperature", level_type=103, level=2,
    start_time=cycle, output_dir=output_root / "level", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in level_paths]
```

选择 `getNafpFileByElementAndTimeAndLevel`，实际下载 `level/level.bin`，大小 5 字节。

(mf-012)=
## 要素加单一预报时效

`forecast_time="24h"` 生成 `validTime="24"`，不是绝对有效日期。
时效也可以用 pandas 或标准库 timedelta，但必须为非负整数小时。
下面仍只指定层次类型，不指定具体层次：

```{code-cell} ipython3
lead_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", parameter="synthetic_temperature", level_type=103,
    start_time=cycle, forecast_time="24h", output_dir=output_root / "lead",
    client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in lead_paths]
```

选择 `getNafpFileByElementAndTimeAndValidtime`，实际下载 `lead/lead.bin`，大小 4 字节。

(mf-019)=
### 要素、具体层次和时效

```{code-cell} ipython3
level_lead_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", parameter="synthetic_temperature", level_type=103, level=2,
    start_time=cycle, forecast_time="24h", output_dir=output_root / "level_lead",
    client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in level_lead_paths]
```

选择 `getNafpFileByElementAndTimeAndLevelAndValidtime`，实际生成
`level_lead/level-lead.bin`，大小 10 字节。没有独立的成员 number 参数。

## 普通文件的时效过滤与 data_type 边界

当 parameter、level_type、level 都未传时，时效不添加专用 validTime 接口，
而生成 `eleValueRanges="Validtime_C:'024'"`，继续使用普通时次/时间段文件接口。
是否支持该条件仍依赖所选资料；这不是本地按文件名裁剪。

`data_type` 是兼容参数，当前没有参与接口选择或校验；`analysis` 不会切换到分析文件
接口。下面特意传 analysis，精确模拟路由证明仍使用 `getNafpFileByTime`；
不能将其解释为已经验证分析资料下载。

```{code-cell} ipython3
filtered_paths = download_model_file(
    "SYNTHETIC_MODEL_FILES", start_time=cycle, forecast_time="24h", count=1,
    data_type="analysis", output_dir=output_root / "filtered", client=client, strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in filtered_paths]
```

实际下载 `filtered/filtered.bin`，大小 8 字节。区分预报/分析须核对 data_code 与具体
文件接口能力，不能直接套用 {doc}`模式格点 <grid>` 的 data_type 切换语义。

(mfl-001)=
## latest 是时次表格，不能直接下载

latest 契约已在 B11 后续复验明确：`getNafpLatestTime` 经 `callAPI_to_array2D`
返回一列 Datetime，经 fileList 曾得到 `-10002`。MFL-001 已记录时次表格在线通过，
不属于七种下载通过；下载函数传相对 Timedelta 会在请求前拒绝。

下面用同一合成真实客户端直接展示独立的底层表格查询：

```{code-cell} ipython3
latest_params = {"dataCode": "SYNTHETIC_MODEL_FILES", "latestTime": "72"}
latest_response = client.callAPI_to_array2D("getNafpLatestTime", latest_params)
latest_response.raise_for_error(interface_id="getNafpLatestTime", params=latest_params)
latest_table = latest_response.to_pandas()
print(latest_table)
print(latest_table.attrs)
```

人工结果为 `Datetime="20260102060000"` 字符串，只有一行；没有生成文件。
这里 latestTime=72 是相对小时数，固定返回仅用于人工演示，不表示运行时最近 72 小时。
真实既有记录用 `NAFP_ANA_FTM_GRAPES_GFS_NEHE` 与相对 72 小时查询时次表；
获得明确时次后，仍须核对选定资料是否支持所需文件接口再下载。

## 成功空清单与服务错误

成功空清单返回 []，不会发起文件 URL 请求，也不创建指定输出子目录：

```{code-cell} ipython3
empty_paths = download_model_file(
    "SYNTHETIC_EMPTY", start_time=cycle, count=1, output_dir=output_root / "empty",
    client=client, strict=True,
)
print(empty_paths, "输出目录是否存在：", (output_root / "empty").exists())
```

默认 strict=False 服务错误返回 MusicError，遍历路径前应检查类型。
严格模式抛结构化 CMADaaSError；下面 -5234 仅是人工清单错误码，此例没有文件下载：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failed_code = None
try:
    download_model_file(
        "SYNTHETIC_ERROR", start_time=cycle, count=1, output_dir=output_root / "error",
        client=client, strict=True,
    )
except CMADaaSError as error:
    failed_code = error.error_code
    print(type(error).__name__, error.error_code, error.interface_id)
    print("是否产生文件：", (output_root / "error").exists())
else:
    raise AssertionError("failed file lists must raise in strict mode")
```

## 参数与对应底层接口

| 参数 | 当前行为 |
| --- | --- |
| data_code | 匹配具体文件接口与权限的资料代码 |
| parameter | 字符串生成 fcstEle 并选择要素接口；非空字符串列表只以点号连接为 elements，不等同于要素接口 |
| start_time | pandas/标准库时次生成 time；Interval 生成 timeRange；相对时长下载拒绝 |
| forecast_time | 单一整数小时时效；要素查询生成 validTime，普通无要素/无层次查询生成 eleValueRanges |
| level_type / level | 要素查询必需层次类型，具体 level 可省略；指定 level 时须配对，具体层次仅支持要素加单时次 |
| region | 参数保留，但矩形/行政区/流域均无模式文件登记，不能据签名认定可用 |
| data_type | 当前不影响接口选择，不提供格点式分析切换 |
| count | 正整数，仅普通时次/时间段接口支持，生成字符串 limitCnt；不是字节上限 |
| output_dir | 本地字符串或 Path，None 使用当前目录；实际写文件时创建父目录 |
| config / client | CedarKit 配置对象/YAML 或已有客户端；显式 client 优先 |
| strict | 默认错误返回 MusicError，True 抛结构化服务异常；本地错误直接抛异常 |

parameter 列表如 `["TEM","RH"]` 仅映射为 `elements="TEM.RH"` 并保留普通文件路由，
不生成 fcstEle，不自动查询两个要素文件；具体服务是否接受须另核对。
起报时间列表虽会生成 times，但当前时次接口必需 time，本地缺参检查拒绝。
本函数没有 `**kwargs`、本地 overwrite/大小开关，不接受模式点的时效范围 tuple。

| 查询条件 | 底层 interface | 案例 |
| --- | --- | --- |
| 起报时次 | `getNafpFileByTime` | MF-003 |
| 起报时间段 | `getNafpFileByTimeRange` | MF-004 |
| 要素 + 时次（必需 levelType） | `getNafpFileByElementAndTime` | MF-008 |
| 要素 + 时间段（必需 levelType） | `getNafpFileByElementAndTimeRange` | MF-009 |
| 要素 + 时次 + 层次 | `getNafpFileByElementAndTimeAndLevel` | MF-010 |
| 要素 + 时次 + 时效（必需 levelType） | `getNafpFileByElementAndTimeAndValidtime` | MF-012 |
| 要素 + 时次 + 层次 + 时效 | `getNafpFileByElementAndTimeAndLevelAndValidtime` | MF-019 |

底层先用 callAPI_to_fileList 解码 FilesInfo，再按各项 file_url 流式下载。
高层委托 callAPI_to_downFile，返回下载后的本地路径，而不是服务清单。
以下错误均请求前拒绝，且不会写文件：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

element = {"parameter": "synthetic_temperature", "level_type": 103}
for label, selectors, error_type in [
    ("latest 下载", {"start_time": pd.Timedelta(hours=72)}, UnsupportedQueryError),
    ("缺少时间", {}, UnsupportedQueryError),
    ("要素缺层次类型", {"start_time": cycle, "parameter": "synthetic_temperature"}, ValueError),
    ("要素接口传 count", {"start_time": cycle, **element, "count": 1}, ValueError),
    ("非法数量", {"start_time": cycle, "count": 0}, ValueError),
    ("时间段加具体层次", {"start_time": window, **element, "level": 2}, UnsupportedQueryError),
    ("预报时效范围", {"start_time": cycle, "forecast_time": ("6h", "24h")}, TypeError),
    ("起报时间列表缺 time", {"start_time": [cycle]}, ValueError),
    ("矩形", {"start_time": cycle, "region": {
        "type": "rect", "start_longitude": 110, "end_longitude": 111,
        "start_latitude": 30, "end_latitude": 31,
    }}, UnsupportedQueryError),
]:
    calls_before = len(transport.calls)
    try:
        download_model_file(
            "SYNTHETIC_MODEL_FILES", output_dir=output_root / "rejected",
            client=client, strict=True, **selectors,
        )
    except error_type:
        print(label, error_type.__name__, "是否发起请求：", len(transport.calls) != calls_before)
    else:
        raise AssertionError("invalid selectors must fail before a request")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(
    {"single": single_paths, "range": range_paths, "element": element_paths,
     "element_range": element_range_paths, "level": level_paths, "lead": lead_paths,
     "level_lead": level_lead_paths, "filtered": filtered_paths, "empty": empty_paths},
    latest_table, output_root, transport, failed_code,
)
```

## 清理与覆盖行为

八个文件共 56 字节，逐个核对了目录、名称、实际大小和内容。
`.read_bytes()` 仅用于这些极小人工文件，不适合全量读取真实大文件。
验证后清理临时目录，已有 Path 不再指向存在文件：

```{code-cell} ipython3
directory.cleanup()
print("临时目录是否仍存在：", output_root.exists())
```

底层默认 overwrite=True，同名目标会替换；单文件先写临时文件再替换，批量下载非事务，
后续文件失败可能保留先前成功文件。高层没有本地覆盖开关，需保留旧文件时选独立目录，
或使用底层 callAPI_to_downFile(..., overwrite=False)。空清单不创建目录。

## 真实服务替换与下载规模

既有记录于 2026-10-08 验证了全部七个模式文件接口：GFS 的时次/时间段各用
limitCnt=1 下载约 50.1 MB，要素/时次案例约 28.5 MB；REPS 要素/时间段约 207.8 MB，
其余三个扰动成员资料文件各约 1.25 GB。REPS 扩展案例当时有明确的 1.5 GiB 单例
上限，不应将这一规模变成文档构建默认下载；未限制的 GFS 清单曾有 97 个文件。
这些历史结果不保证当前账号和时次可用，本次不重跑在线验证。

真实下载先查相同请求的清单并限制数量及字节数，特别是不能传 count 的要素接口。
下面采用既有 GFS 要素/时次案例，最多 1 文件、32 MiB 已知大小；真实日期按原累计
减三天 06 时计算。此代码需真实服务，不在文档构建时执行：

```python
from pathlib import Path
import pandas as pd
from nuwe_cmadaas.music import create_client
from nuwe_cmadaas.model import download_model_file

real_client = create_client(config="/path/to/cedarkit.yaml")
recent_cycle = (
    (pd.Timestamp.now() - pd.offsets.Day()).normalize()
    - pd.Timedelta(days=2) + pd.Timedelta(hours=6)
)
params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM", "levelType": "103",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"),
}
listing = real_client.callAPI_to_fileList("getNafpFileByElementAndTime", params)
listing.raise_for_error(interface_id="getNafpFileByElementAndTime", params=params)
infos = listing.files_info
if not 0 < len(infos) <= 1 or any(not info.size.isdecimal() for info in infos):
    raise RuntimeError("Expected at most one file with a known byte size")
if sum(int(info.size) for info in infos) > 32 * 1024 * 1024:
    raise RuntimeError("File preflight exceeds 32 MiB")

paths = download_model_file(
    "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", parameter="TEM", level_type=103,
    start_time=recent_cycle, output_dir=Path("./cmadaas-model-files"),
    client=real_client, strict=True,
)
```

预查询与高层下载会再次请求清单，期间服务清单可能改变；高层没有本地总字节上限。
集成测试另用受限清单客户端并核对实际文件，生产使用应按具体清单及大小策略处理。
不能把 REPS 的资料能力外推 GFS，或只按同一模式名称选资料；后续优先目录支持的
GFS，需要 MESO 时选 3KM，不沿用停运的低分辨率 10KM 资料。
配置见 {doc}`高层配置 </guide/configuration/high-level>`，动态日期规则见
{doc}`测试与动态时间 </development/testing>`，两层调用对照见
{doc}`接口选择 </guide/choosing-api>`。

共享源码为 `examples/high_level/model_files.py`，本页复用准备与磁盘断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.model_files
```

脚本默认仅使用合成数据，实际下载七种组合及一个时效过滤变体的八个小文件，
展示独立 latest 表格、空清单、严格业务异常与九种本地错误，校验后自动清理。
无需账号或第二个示例安装包，辅助模块不随 wheel 分发。完整签名见
{py:func}`nuwe_cmadaas.model.download_model_file`；其他模式入口见 {doc}`模式目录 <index>`。
