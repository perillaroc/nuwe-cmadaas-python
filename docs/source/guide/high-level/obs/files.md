---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面观测文件下载

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.obs.download_obs_file` 下载地面观测文件。
成功结果是 `list[pathlib.Path]`，每个路径对应一个已下载文件；它与站点表格、
格点数组和底层 `FilesInfo` 清单是不同的返回类型。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_FILES`、`FAKE001`、固定时次 `2026-01-02` 和 `.invalid` 下载地址仅用于
离线演示；文件内容是人工 bytes，不是真实气象文件，也不说明任何实际文件格式。

本例注入合成 transport 的真实 MUSIC 客户端，先解码文件清单，再流式写入磁盘。
全页在临时目录中执行，最后清理；输出只显示相对文件名、大小和小文件内容，
不把随机绝对路径写入教程。未知请求或下载 URL 立即失败，不回退真实网络。

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

from examples.high_level.files import make_file_client, check_results

client, transport = make_file_client()
directory = TemporaryDirectory()
output_root = Path(directory.name)
```

(of-002)=
## 按时次下载一个文件

`data_code` 选择文件资料，`time` 选择时次，`count=1` 请求最多一条清单记录，
`output_dir` 是本地输出目录。本例用严格模式让服务失败直接抛异常。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import download_obs_file

single_paths = download_obs_file(
    "SYNTHETIC_FILES",
    time=pd.Timestamp("2026-01-02"),
    count=1,
    output_dir=output_root / "single",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in single_paths]
```

结果为 `single/synthetic.bin`，大小 4 字节，内容为 `b"FAKE"`。
这不是由准备代码预写的文件：公开函数调用底层下载流程，从模拟 URL 获取内容并写入磁盘。
该请求选择 `getSurfFileByTime`，原生参数为 `times="20260102000000"`、`limitCnt=1`。

```{code-cell} ipython3
{
    "return_type": type(single_paths).__name__,
    "path_is_Path": isinstance(single_paths[0], Path),
    "file_exists": single_paths[0].is_file(),
}
```

路径按清单顺序返回，以本地 `output_dir` 加服务文件名组成；不会将整个清单转成
DataFrame，也不使用清单的服务端保存路径作为本地目录。
`Path` 的具体实现随平台可能是 `PosixPath` 或 `WindowsPath`，都属于 `pathlib.Path`。
相对输出目录仍返回相对路径；需要绝对位置时自行调用 `.resolve()`。

(of-003)=
## 按时间段下载多个文件

用 `pd.Interval` 明确端点包含关系。下面包含左端零时、排除右端一时，
原生参数是 `timeRange="[20260102000000,20260102010000)"`。

```{code-cell} ipython3
window = pd.Interval(
    pd.Timestamp("2026-01-02"),
    pd.Timestamp("2026-01-02 01:00"),
    closed="left",
)
range_paths = download_obs_file(
    "SYNTHETIC_FILES",
    time=window,
    count=2,
    output_dir=output_root / "range",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in range_paths]
```

底层选择 `getSurfFileByTimeRange`。合成清单有两个文件 `range-a.bin/range-b.bin`，
各 7 字节，内容分别为 `b"RANGE-A"/b"RANGE-B"`；公开函数返回两个 `Path`。
返回多少文件由所选资料和清单决定，不能从时间段长度推断文件数。
真实大文件不宜直接 `.read_bytes()` 全量读入内存，本例仅展示极小的人工内容。

(of-009)=
## 站号必须与时间段组合

地面站号文件当前只登记时间段加站号组合，不能沿用“单时次加站号”的表格查询方式。
`station` 可以是单站或站点列表，映射为 `staIds`。

```{code-cell} ipython3
station_paths = download_obs_file(
    "SYNTHETIC_FILES",
    time=window,
    station="FAKE001",
    count=1,
    output_dir=output_root / "station",
    client=client,
    strict=True,
)
[(path.relative_to(output_root).as_posix(), path.stat().st_size, path.read_bytes())
 for path in station_paths]
```

该请求选择 `getSurfFileByTimeRangeAndStaID`，模拟下载得到 `station.bin`，大小 7 字节。
这一目录接口已有离线案例，但现有账号尚无已确认的匹配资料权限，`OF-009` 仍为
`implemented-unverified` 且默认禁用；合成示例不把它改记为真实服务通过。

## 成功空清单与服务失败

成功的空清单返回 `[]`，不会下载文件，不能与业务错误混为一谈。
下面用独立的人工资料代码构造成功空清单：

```{code-cell} ipython3
empty_paths = download_obs_file(
    "SYNTHETIC_EMPTY",
    time=pd.Timestamp("2026-01-02"),
    count=1,
    output_dir=output_root / "empty",
    client=client,
    strict=True,
)
empty_paths
```

不要仅因为指定了 `output_dir` 就假定目录一定存在；目录在实际写文件时创建。
服务报错时，默认 `strict=False` 返回 `MusicError`，应先检查返回类型再遍历路径。
`strict=True` 则抛结构化 `CMADaaSError`；这里的 `-1234` 仅是合成错误码：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failed_code = None
try:
    download_obs_file(
        "SYNTHETIC_ERROR",
        time=pd.Timestamp("2026-01-02"),
        count=1,
        output_dir=output_root / "error",
        client=client,
        strict=True,
    )
except CMADaaSError as error:
    failed_code = error.error_code
    print(type(error).__name__, error.error_code, error.interface_id)
    print("是否产生文件：", (output_root / "error").exists())
else:
    raise AssertionError("failed file lists must raise in strict mode")
```

此例在清单阶段失败，没有发起文件 URL 请求或产生磁盘文件。
如果真实批量下载在后续文件失败，先前下载成功的文件可能仍留在输出目录，
整个批次不是事务；应检查已完成文件并按业务需要恢复或清理。

(ofl-001)=
## 参数与当前能力边界

| 参数 | 当前用法 |
| --- | --- |
| `data_code` | 与文件接口及账号权限匹配的资料代码，不是表格要素资料的通用替代 |
| `time` | `pd.Timestamp` / `datetime` 或非空时间列表生成 `times`；`pd.Interval` 生成 `timeRange` |
| `station` | 单站字符串/整数或非空站号列表生成 `staIds`；必须配合时间段 |
| `elements` / `order` | 可选服务字段/排序参数；原样传递，不自动读取站点资料的要素配置 |
| `count` | 正整数，生成 `limitCnt`；由服务支持该参数，不是本地文件大小上限 |
| `output_dir` | 本地字符串或 Path 目录；实际写文件时创建父目录，返回目录与文件名组合的 Path |
| `region` / `station_level` | 没有对应的地面区域/专用等级文件登记；参数能规范化不代表资料支持 |
| `interface_data_type` | 默认 `Surf`；`Upar` 属于高空文件包装路径，具体查询组合不同 |
| `config` / `client` | CedarKit YAML 路径或字典 / 已有客户端；显式 `client` 优先 |
| `strict` | 默认兼容 `MusicError`；`True` 在服务错误时抛结构化异常 |
| `**kwargs` | 传给所选 MUSIC 接口的额外参数，不是任意本地下载选项 |

当前地面文件下载只登记三类组合：

| 查询条件 | 底层 interface |
| --- | --- |
| 时次 | `getSurfFileByTime` |
| 时间段 | `getSurfFileByTimeRange` |
| 时间段 + 单站/站点列表 | `getSurfFileByTimeRangeAndStaID` |

时间列表能在本地映射为 `times`，资料是否接受多个时次须另行核对。
未传时间、单时次加站号、站号范围、矩形/行政区/流域等组合在请求前拒绝。
相对 `Timedelta` 会报 `UnsupportedQueryError`：`getSurfLatestTime` 是 `Datetime` 表格，
不能当作文件清单下载。最新时次的表格用法见 {doc}`地面站点 <station>`；
独立时次表案例 `OFL-001` 的既有通过记录也不代表下载接口支持 latest。

下面复现 latest、单时次加站号和非法数量错误，均不会发起传输请求：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

for label, selectors, error_type in [
    ("latest 下载", {"time": pd.Timedelta(hours=6)}, UnsupportedQueryError),
    ("单时次加站号", {"time": pd.Timestamp("2026-01-02"), "station": "FAKE001"},
     UnsupportedQueryError),
    ("非法数量", {"time": pd.Timestamp("2026-01-02"), "count": 0}, ValueError),
]:
    calls_before = len(transport.calls)
    try:
        download_obs_file(
            "SYNTHETIC_FILES", output_dir=output_root / "rejected",
            client=client, strict=True, **selectors,
        )
    except error_type as error:
        print(label, type(error).__name__, "是否发起请求：", len(transport.calls) != calls_before)
    else:
        raise AssertionError("invalid selectors must fail before a request")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(
    {"single": single_paths, "range": range_paths, "station": station_paths, "empty": empty_paths},
    output_root, transport, failed_code,
)
```

## 清理目录与同名文件行为

所有输出在临时目录中，验证完成后明确清理。清理之后返回的 Path 不再指向存在的文件：

```{code-cell} ipython3
directory.cleanup()
print("临时目录是否仍存在：", output_root.exists())
```

当前高层调用底层 `callAPI_to_downFile`，使用默认 `overwrite=True`；已有同名目标文件
会被替换。每个文件采用临时文件写入后替换的流程，不能把这一行为当作整个批次的回滚。
高层没有独立的 `overwrite` 开关；把它传入 `**kwargs` 会变成服务参数，不能控制本地覆盖。
需要保留已有文件时使用独立输出目录，或用底层 `callAPI_to_downFile(..., overwrite=False)`。

## 对应底层流程与真实服务替换

底层先获取 `FilesInfo.files_info`，再从每项的 `file_url` 流式下载；
签名请求沿用 `callAPI_to_fileList` 方法名。只查询清单不会产生文件，
高层的 Path 是下载完成后的本地结果。更多模拟实现见专章。

真实下载前限定时次和数量，并先检查相同查询的文件清单及总字节数。
高层没有本地总字节上限，`count=1` 也不能限制单个文件大小。
下面采用已有成功记录中的 `SURF_CMPA_FRT_5KM_10MIN` 和运行日期两天前的时次，
先验证最多 1 文件、合计不超过 10 MiB；实际仍需账号权限和对应数据。
以下代码需真实服务，不在文档构建时执行：

```python
from nuwe_cmadaas.music import create_client

real_client = create_client(config="/path/to/cedarkit.yaml")
recent_time = pd.Timestamp.now().normalize() - pd.Timedelta(days=2)
params = {
    "dataCode": "SURF_CMPA_FRT_5KM_10MIN",
    "times": recent_time.strftime("%Y%m%d%H%M%S"),
    "limitCnt": 1,
}
listing = real_client.callAPI_to_fileList("getSurfFileByTime", params)
listing.raise_for_error(interface_id="getSurfFileByTime", params=params)
infos = listing.files_info
if not 0 < len(infos) <= 1 or any(not info.size.isdecimal() for info in infos):
    raise RuntimeError("Expected at most one file with a known byte size")
if sum(int(info.size) for info in infos) > 10 * 1024 * 1024:
    raise RuntimeError("File preflight exceeds 10 MiB")

paths = download_obs_file(
    "SURF_CMPA_FRT_5KM_10MIN",
    time=recent_time,
    count=1,
    output_dir=Path("./cmadaas-files"),
    client=real_client,
    strict=True,
)
```

预查询与下载是两次请求，不能保证期间服务清单完全不变。
现有集成测试另有严格清单和大小检查；服务可能变化时按实际清单和文件验证结果处理。
`OF-002/OF-003` 有真实下载通过记录，站号案例 `OF-009` 仍待匹配权限，本页不重跑在线案例。
配置说明见 {doc}`高层配置 </guide/configuration/high-level>`，动态日期规则见
{doc}`测试与动态时间 </development/testing>`，两层调用区别见
{doc}`接口选择 </guide/choosing-api>`。

## 取得并运行完整示例

共享源码为 `examples/high_level/files.py`，本页复用客户端准备和磁盘结果断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.files
```

脚本默认仅使用合成数据，验证三个下载组合、四个真实生成的小文件、成功空清单、
严格服务异常和三个本地错误，打印相对名称/大小/内容后清理临时目录。
辅助代码不随 wheel 分发，不需要第二个示例安装包。
完整签名见 {py:func}`nuwe_cmadaas.obs.download_obs_file`；
观测表格见 {doc}`地面站点 <station>`，二维场见 {doc}`地面格点 <grid>`。
