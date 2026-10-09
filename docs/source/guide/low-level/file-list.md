---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层文件清单：FilesInfo 与 FileInfo

## 用途与示例来源

用 {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_fileList` 查询文件名称、
大小和下载地址，先了解结果规模，再决定是否下载。返回 `FilesInfo`，其中
`files_info` 是 `FileInfo` 对象列表；查询不读取文件正文、不创建下载目录。
下载流程见 {doc}`底层文件下载 <downloads>`，业务层文件筛选见
{doc}`模式文件指南 </guide/high-level/model/files>`。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 MUSIC 客户端经注入的 `SyntheticTransport` 读取人工 RetFilesInfo protobuf，
运行生产解码；未知请求立即失败，没有网络回退，不替换公开方法。
SYNTHETIC 资料/要素、固定起报时次和 `.invalid` 地址均为演示值。
两项清单描述 first.bin（4 字节）与 second.bin（6 字节），它们是人工小文件，
不是实际气象文件。此页只查询清单，即使 transport 登记了正文也不会下载。

## 原生参数与准备

| 参数 | 本例值与含义 |
| --- | --- |
| interface_id | `getNafpFileByElementAndTime`，支持 RetFilesInfo 的文件接口 |
| dataCode / fcstEle | `SYNTHETIC_FILES` / `synthetic_temperature`，资料与要素 |
| time | `"20260102060000"`，原生起报时次字符串 |
| levelType | `"103"`，本例高度层类型；本接口不必传具体 fcstLevel |
| server_id | 可选方法参数，省略则使用客户端节点，显式值覆盖本次请求 |

底层不将高层 `parameter/start_time/count` 转成服务参数，不修改 params，
也不按高层登记自动校验查询组合。本页不传 limitCnt；是否支持数量、
时间段或站号筛选需要逐接口核对。签名、账号等封装字段由客户端构造。

```{code-cell} ipython3
:tags: [hide-input]

import os
import sys
from pathlib import Path

start = Path(os.environ.get("NUWE_CMADAAS_REPO_ROOT", Path.cwd())).resolve()
repo_root = next(
    (path for path in (start, *start.parents)
     if (path / "examples" / "_support" / "synthetic.py").is_file()),
    None,
)
if repo_root is None:
    raise RuntimeError("Run this example from a nuwe-cmadaas-python checkout")
sys.path.insert(0, str(repo_root))

from examples.music.files import make_file_client, check_listing_results

client, transport = make_file_client()
```

(llf-001)=
## 查询状态与文件信息

下面显式创建一个空临时目录，仅用于核对查询没有写文件，目录不是 fileList 创建的：

```{code-cell} ipython3
from tempfile import TemporaryDirectory
from nuwe_cmadaas.music import CMADaaSClient

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
interface_id = "getNafpFileByElementAndTime"
params = {
    "dataCode": "SYNTHETIC_FILES", "fcstEle": "synthetic_temperature",
    "levelType": "103", "time": "20260102060000",
}
listing = client.callAPI_to_fileList(interface_id, params)
listing.raise_for_error(interface_id=interface_id, params=params)
{
    "response_type": type(listing).__name__, "ok": listing.ok,
    "error_code": listing.request.error_code, "file_count": len(listing.files_info),
    "request_counts": (listing.request.row_count, listing.request.col_count),
    "local_files": [path.name for path in output_root.iterdir()],
}
```

成功返回两个 FileInfo，错误码为零，临时目录仍为空。
`ok` 只依据错误码，不能保证文件正文可下载或元数据完整。
本例 RequestInfo 的 row_count/col_count 为 2/1，是人工响应的统计，
使用清单时应直接检查 len(files_info)，不当成表格或格点尺寸。

```{code-cell} ipython3
import pandas as pd

records = [{
    "type": type(info).__name__, "file_name": info.file_name,
    "size": info.size, "suffix": info.suffix, "save_path": info.save_path,
    "file_url": info.file_url, "image_base64": info.image_base64,
    "attributes": info.attributes,
} for info in listing.files_info]
pd.DataFrame(records)
```

这个 DataFrame 是为展示 FileInfo 字段而创建的，API 返回值仍是 FilesInfo。

| 字段 | 使用方式与边界 |
| --- | --- |
| file_name | 服务文件名，本例 first.bin / second.bin；查询本身不证明名称适合本地写入 |
| size | **字符串** `"4"/"6"`；本例按字节定义，真实字段可能空或非数字，验证后再转 int |
| suffix | 服务提供的后缀字符串，本例 `"bin"`；不自动补点号或标准化 |
| save_path | 服务返回的路径描述；本例 `/synthetic/service/...`，不是本地文件或 Path |
| file_url | 下载地址，本页只有人工 `.invalid` URL；真实地址可能含认证信息，避免直接公开 |
| image_base64 / attributes | 响应字段，本例为空字符串 / `['synthetic','offline']`，不能推断所有资料都有这些值 |

```{code-cell} ipython3
{
    "size_types": [type(info.size).__name__ for info in listing.files_info],
    "known_total_bytes": sum(int(info.size) for info in listing.files_info),
    "metadata": listing.metadata,
    "request_time": listing.request.request_time,
    "response_time": listing.request.response_time,
    "binary_transfers": sum(response.streamed for response in transport.responses),
}
```

已知大小合计 10 字节，正文传输为零。FilesInfo.metadata 有 interface_id、time 和
level_type，响应时间在 request 中；FilesInfo 没有 DataFrame 的 attrs，也不是高层
下载函数返回的 list[Path]。这里的服务路径、大小和 URL 都是元数据，未核对磁盘内容。

## 成功空清单与服务失败

```{code-cell} ipython3
empty_params = {**params, "dataCode": "SYNTHETIC_EMPTY"}
empty = client.callAPI_to_fileList(interface_id, empty_params)
empty.raise_for_error(interface_id=interface_id, params=empty_params)
{"ok": empty.ok, "files_info": empty.files_info, "local_files": list(output_root.iterdir())}
```

成功空清单为 `ok=True` 和 `[]`，与服务失败分开处理。底层没有 `strict=`：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSRequestError

failed_params = {**params, "dataCode": "SYNTHETIC_ERROR"}
failed = client.callAPI_to_fileList(interface_id, failed_params)
try:
    failed.raise_for_error(interface_id=interface_id, params=failed_params)
except CMADaaSRequestError as error:
    print("ok:", failed.ok, type(error).__name__, error.error_code, error.interface_id)
else:
    raise AssertionError("service failure must raise")
```

处理过的服务、传输或解码失败记录在 request，先检查状态再使用列表；
本地配置/参数错误仍可能直接抛出。不要仅凭 files_info 为空判断请求成功。

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
check_listing_results({"listing": listing, "empty": empty, "failed": failed},
                      output_root, transport, params)
```

```{code-cell} ipython3
workspace.cleanup()
print("临时目录已清理：", not output_root.exists())
```

## 真实服务替换与完整示例

LLF-001 于 2026-10-08 使用 GFS 预报资料 `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE`、
TEM、高度层类型 103 和动态三天前 06 时查询通过：一项 GRIB2 清单，
size 为 `"28492363"`，未下载正文。本次保留既有记录，不将人工两文件清单记为
新的在线验证；资料、权限、近期时次和返回规模仍需真实环境核对。

下面只查询清单，不下载。需要真实 INI、账号与服务，**不在文档构建时执行**：

```python
import pandas as pd
from nuwe_cmadaas.music import CMADaaSClient

real_client = CMADaaSClient(
    config_file="/path/to/client.config", user="YOUR_USER", password="YOUR_PASSWORD",
    log_policy="redacted",
)
recent_cycle = (
    (pd.Timestamp.now() - pd.offsets.Day()).normalize()
    - pd.Timedelta(days=2) + pd.Timedelta(hours=6)
)
real_interface_id = "getNafpFileByElementAndTime"
real_params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM", "levelType": "103",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"),
}
real_listing = real_client.callAPI_to_fileList(real_interface_id, real_params)
real_listing.raise_for_error(interface_id=real_interface_id, params=real_params)
file_names = [info.file_name for info in real_listing.files_info]
```

下载前的数量与已知字节规模检查见 {doc}`底层文件下载 <downloads>`；
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，
日期和案例见 {doc}`测试与动态时间 </development/testing>`，完整签名见
{doc}`客户端参考 </reference/client>`。

在源码仓库根目录运行共享脚本，独立验证本页以及下载页：

```bash
uv run python -m examples.music.files
```

`examples/music/files.py` 的清单示例实际执行三次查询，验证无正文传输或磁盘写入，
并清理用于检查的临时目录；无需配置或账号。
