---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 高空观测文件下载

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.obs.download_obs_upper_air_file` 下载高空观测文件。
包装函数固定使用 `Upar` 文件接口族，成功返回 `list[pathlib.Path]`，
每个 Path 指向实际下载的本地文件；结果不是高空表格或底层 `FilesInfo` 清单。
本页独立演示四种已登记查询，包含地面文件未登记的“单时次加站号”组合。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_UPPER_FILES`、`FAKE001/FAKE002`、固定时次 `2026-01-02` 和 `.invalid`
地址仅用于离线演示。小文件内容是人工 bytes，不代表真实高空气象文件或其格式。

这里注入合成 transport 的真实 MUSIC 客户端，经 protobuf 解码清单、流式下载并写入
临时目录。准备阶段不预写文件，也不替换公开下载函数；未知请求或 URL 立即失败，
不回退真实网络。输出只展示相对名称、大小和小文件内容，最后显式清理。

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

from examples.high_level.upper_air_files import make_upper_file_client, check_results

client, transport = make_upper_file_client()
directory = TemporaryDirectory()
output_root = Path(directory.name)
```

(ouf-002)=
## 按时次下载

`data_code` 是文件资料代码，`time` 是文件时次，`count=1` 请求最多一条清单记录，
`output_dir` 是本地目录。严格模式把服务错误转为异常。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import download_obs_upper_air_file

time = pd.Timestamp("2026-01-02")
single_paths = download_obs_upper_air_file(
    "SYNTHETIC_UPPER_FILES",
    time=time,
    count=1,
    output_dir=output_root / "single",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in single_paths]
```

请求选择 `getUparFileByTime`，返回 `single/upper.bin`，大小 5 字节，内容 `b"UPPER"`。
下面直接检查结果类型和磁盘存在性；具体 Path 子类名随操作系统变化：

```{code-cell} ipython3
{
    "返回列表": isinstance(single_paths, list),
    "元素为 Path": all(isinstance(path, Path) for path in single_paths),
    "文件存在": all(path.is_file() for path in single_paths),
}
```

(ouf-003)=
## 按时间段下载

`pd.Interval` 的左右端点和闭合方式生成服务 `timeRange`。
本例采用左闭右开的一小时区间，请求仍限定最多一个文件：

```{code-cell} ipython3
window = pd.Interval(time, time + pd.Timedelta(hours=1), closed="left")
range_paths = download_obs_upper_air_file(
    "SYNTHETIC_UPPER_FILES",
    time=window,
    count=1,
    output_dir=output_root / "range",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in range_paths]
```

请求选择 `getUparFileByTimeRange`，`timeRange` 为 `[20260102000000,20260102010000)`，
实际下载 `range/range.bin`，大小 5 字节。清单决定文件数，不能由时间段长度推断。

(ouf-007)=
## 单时次加站号

高空文件允许时次加站号，不能套用地面文件必须使用时间段的限制。
单站字符串生成 `staIds`，本例选择 `getUparFileByTimeAndStaID`：

```{code-cell} ipython3
station_paths = download_obs_upper_air_file(
    "SYNTHETIC_UPPER_FILES",
    time=time,
    station="FAKE001",
    count=1,
    output_dir=output_root / "station",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in station_paths]
```

实际下载 `station/station.bin`，大小 7 字节，内容 `b"STATION"`。

(ouf-009)=
## 时间段加站点列表

站点列表合并为逗号分隔的 `staIds`，本例为 `FAKE001,FAKE002`。
元组表示站号范围，与列表含义不同；目前站号范围没有高空文件登记。

```{code-cell} ipython3
station_range_paths = download_obs_upper_air_file(
    "SYNTHETIC_UPPER_FILES",
    time=window,
    station=["FAKE001", "FAKE002"],
    count=1,
    output_dir=output_root / "station_range",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in station_range_paths]
```

请求选择 `getUparFileByTimeRangeAndStaID`，实际下载 `station_range/window.bin`，
大小 6 字节，内容 `b"WINDOW"`。这里的列表转换通过合成请求验证，
不意味着每种真实资料都支持多个站号。

## 成功空清单与服务错误

成功空清单返回 `[]`，没有文件下载，也不创建指定的子目录：

```{code-cell} ipython3
empty_paths = download_obs_upper_air_file(
    "SYNTHETIC_EMPTY", time=time, count=1, output_dir=output_root / "empty",
    client=client, strict=True,
)
print(empty_paths, "输出目录是否存在：", (output_root / "empty").exists())
```

默认 `strict=False` 的服务错误返回 `MusicError`，应先检查类型再遍历路径。
`strict=True` 抛结构化 `CMADaaSError`。下面的 `-1234` 仅为合成业务错误码，
此例在清单阶段失败，没有请求文件 URL：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failed_code = None
try:
    download_obs_upper_air_file(
        "SYNTHETIC_ERROR", time=time, count=1, output_dir=output_root / "error",
        client=client, strict=True,
    )
except CMADaaSError as error:
    failed_code = error.error_code
    print(type(error).__name__, error.error_code, error.interface_id)
    print("是否产生文件：", (output_root / "error").exists())
else:
    raise AssertionError("failed file lists must raise in strict mode")
```

## 参数与能力边界

| 参数 | 当前用法 |
| --- | --- |
| `data_code` | 与高空文件接口及账号权限匹配的资料代码，不自动加载表格要素配置 |
| `time` | pandas/标准库时次或非空时间列表生成 `times`；Interval 生成 `timeRange` |
| `station` | 单站或非空列表生成 `staIds`；时次和时间段均有站号组合 |
| `elements` / `order` | 可选服务字段 / 排序，生成 `elements` / `orderby`，不控制本地文件格式 |
| `count` | 正整数，生成 `limitCnt`，不是文件字节上限 |
| `output_dir` | 本地字符串或 Path；实际写文件时创建父目录，返回目录与文件名组合的 Path |
| `config` / `client` | CedarKit 配置或已有 MUSIC 客户端；显式 `client` 优先 |
| `strict` | 默认兼容 MusicError；True 时在服务错误抛结构化异常 |
| `**kwargs` | 额外 MUSIC 服务参数，不是本地覆盖或下载大小选项 |

包装函数固定 `interface_data_type="Upar"`，调用者不要额外传入这个参数。
已登记查询完整如下；时间列表仅确认本地 `times` 映射，多时次服务能力须另行核对。

| 查询条件 | 底层 interface |
| --- | --- |
| 时次 | `getUparFileByTime` |
| 时间段 | `getUparFileByTimeRange` |
| 时次 + 单站/站点列表 | `getUparFileByTimeAndStaID` |
| 时间段 + 单站/站点列表 | `getUparFileByTimeRangeAndStaID` |

未指定时间、站号范围、矩形/行政区/流域、专用站点等级没有对应的高空文件组合。
相对 Timedelta 用于最新时次表格，文件下载在请求前拒绝；查找最新时次可参考
{doc}`高空观测 <upper-air>`，随后用明确时次请求文件。
下面展示 latest、缺少时间、站号范围和非法数量错误，并证明没有新增传输请求：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

for label, selectors, error_type in [
    ("latest 下载", {"time": pd.Timedelta(hours=6)}, UnsupportedQueryError),
    ("缺少时间", {}, UnsupportedQueryError),
    ("站号范围", {"time": time, "station": ("FAKE001", "FAKE002")}, UnsupportedQueryError),
    ("非法数量", {"time": time, "count": 0}, ValueError),
]:
    calls_before = len(transport.calls)
    try:
        download_obs_upper_air_file(
            "SYNTHETIC_UPPER_FILES", output_dir=output_root / "rejected",
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
    {"single": single_paths, "range": range_paths, "station": station_paths,
     "station_range": station_range_paths, "empty": empty_paths},
    output_root, transport, failed_code,
)
```

## 清理与覆盖行为

四个下载文件共 23 字节，断言已检查每个 Path 的目录、名称、实际大小和内容。
`.read_bytes()` 只用于展示这里的极小人工内容，不适合全量读取真实大文件。
现在清理临时目录，清理后的 Path 不再指向存在的文件：

```{code-cell} ipython3
directory.cleanup()
print("临时目录是否仍存在：", output_root.exists())
```

底层采用默认 `overwrite=True`，已有同名文件会被替换。单文件写临时文件后替换，
批量下载不是事务，后续失败可能留下已成功下载的文件。
高层没有本地 `overwrite` 开关，kwargs 中同名字段只会成为服务参数。
需要保留旧文件时使用独立目录，或使用底层 `callAPI_to_downFile(..., overwrite=False)`。

## 底层对应与真实服务替换

包装函数委托公共文件下载逻辑，以固定 Upar 接口族解析查询组合，再调用
`callAPI_to_downFile`。客户端用 `callAPI_to_fileList` 获取 `FilesInfo.files_info`，
随后从各 `file_url` 流式写入本地。只获取清单不会产生文件，高层 Path 是下载后的结果。
共用流程也见 {doc}`地面文件 <files>`；本页的四次高空调用各自执行和验证。

已有 `OUF-002/OUF-003/OUF-007/OUF-009` 真实通过记录均使用 `UPAR_WPR_STATUS`，
站号组合使用 `54511`，日期为运行日两天前的时次或一小时窗口，最多 1 文件和 10 MiB。
记录核验于 2026-10-08，不代表其他资料、账号、站号或当前日期也一定可用；
本次文档执行不重跑真实服务，不把合成成功算作新的在线验证。

替换客户端时还需替换资料、站号及动态日期。`count=1` 不能限制单个文件大小，
下载前先检查相同请求的文件清单。以下代码需真实服务，不在文档构建时执行：

```python
from pathlib import Path
import pandas as pd
from nuwe_cmadaas.music import create_client
from nuwe_cmadaas.obs import download_obs_upper_air_file

real_client = create_client(config="/path/to/cedarkit.yaml")
recent_time = pd.Timestamp.now().normalize() - pd.Timedelta(days=2)
params = {
    "dataCode": "UPAR_WPR_STATUS",
    "times": recent_time.strftime("%Y%m%d%H%M%S"),
    "staIds": "54511",
    "limitCnt": 1,
}
listing = real_client.callAPI_to_fileList("getUparFileByTimeAndStaID", params)
listing.raise_for_error(interface_id="getUparFileByTimeAndStaID", params=params)
infos = listing.files_info
if not 0 < len(infos) <= 1 or any(not info.size.isdecimal() for info in infos):
    raise RuntimeError("Expected at most one file with a known byte size")
if sum(int(info.size) for info in infos) > 10 * 1024 * 1024:
    raise RuntimeError("File preflight exceeds 10 MiB")

paths = download_obs_upper_air_file(
    "UPAR_WPR_STATUS", time=recent_time, station="54511", count=1,
    output_dir=Path("./cmadaas-upper-files"), client=real_client, strict=True,
)
```

预查询和高层下载是两次清单请求，服务清单可能在期间改变；高层没有本地总字节上限。
集成测试另外采用受限清单客户端并校验实际文件，生产使用应按具体清单和大小策略处理。
配置见 {doc}`高层配置 </guide/configuration/high-level>`，动态时间规则见
{doc}`测试与动态时间 </development/testing>`，两层调用区别见
{doc}`接口选择 </guide/choosing-api>`。

## 取得并运行完整示例

完整脚本为 `examples/high_level/upper_air_files.py`；本页复用其客户端准备和磁盘断言。
取得源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.upper_air_files
```

脚本默认使用合成数据，验证四个下载组合、成功空清单、严格服务错误和四个本地错误，
打印相对名称、大小与内容后自动清理。辅助模块不随 wheel 分发，无需第二个示例安装包。
完整签名见 {py:func}`nuwe_cmadaas.obs.download_obs_upper_air_file`；
高空表格见 {doc}`高空观测 <upper-air>`，其他观测入口见 {doc}`观测目录 <index>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。
