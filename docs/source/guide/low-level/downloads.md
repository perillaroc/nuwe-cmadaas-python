---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层文件下载：目录、覆盖与实际结果

## 用途与示例来源

用 {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_downFile` 查询文件清单并
将正文下载到本地目录。返回仍是 `FilesInfo`，本地路径需按 file_dir/file_name 构造，
核对实际文件；高层下载函数返回的 list[Path] 见
{doc}`模式文件指南 </guide/high-level/model/files>`。
只需看元数据时使用 {doc}`底层文件清单 <file-list>`。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 MUSIC 客户端经精确 `SyntheticTransport` 解码人工 RetFilesInfo，运行生产流式
下载和磁盘写入；未知请求立即失败，没有网络回退，不替换公开方法。
first.bin 正文为 `b'FAKE'`（4 字节），second.bin 为 `b'SECOND'`（6 字节），
均是人工小文件。准备阶段不预写下载结果，调用发生在可见单元中。

## 原生参数与准备

原生 interface 与业务参数和清单页相同：getNafpFileByElementAndTime，
dataCode/fcstEle/levelType/time。本方法不修改 params、不翻译高层参数，也没有 strict。
file_dir 接受 str 或 Path；server_id 可选，覆盖本次清单请求的节点。

| 参数 | 行为 |
| --- | --- |
| file_dir | 本地目标目录，每项按 file_dir / FileInfo.file_name 写入；开始下载时创建父目录 |
| overwrite=True（默认） | 下载后替换已有目标 |
| overwrite=False | 遇到已有目标返回下载错误并停止，不是跳过已有文件继续 |

下载会重新调用 fileList，然后依清单顺序下载；不会直接复用之前取得的 FilesInfo。
客户端拒绝空名、点目录或含路径分隔符的服务文件名。
FileInfo.save_path 保留服务返回的描述，不更新为本地路径。

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

from examples.music.files import make_file_client, check_download_results

client, transport = make_file_client()
```

(llf-002)=
## 先查询，再实际下载

创建临时目录并展示本次请求。这个人工清单已知含两文件、10 字节，不等于真实服务
具备相同规模或数量上限：

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
preflight = client.callAPI_to_fileList(interface_id, params)
preflight.raise_for_error(interface_id=interface_id, params=params)
{
    "file_count": len(preflight.files_info),
    "known_bytes": sum(int(info.size) for info in preflight.files_info),
    "local_files": [path.name for path in output_root.iterdir()],
}
```

```{code-cell} ipython3
downloaded = client.callAPI_to_downFile(
    interface_id, params, file_dir=output_root / "main", overwrite=False,
)
downloaded.raise_for_error(interface_id=interface_id, params=params)
{
    "response_type": type(downloaded).__name__, "ok": downloaded.ok,
    "file_count": len(downloaded.files_info),
    "response_save_paths": [info.save_path for info in downloaded.files_info],
}
```

按目标目录和服务文件名计算 Path，读取实际大小与正文，而不是根据元数据假定写入成功：

```{code-cell} ipython3
paths = [output_root / "main" / info.file_name for info in downloaded.files_info]
[(path.relative_to(output_root).as_posix(), path.exists(), path.stat().st_size, path.read_bytes())
 for path in paths]
```

结果是 main/first.bin（4 字节 FAKE）和 main/second.bin（6 字节 SECOND）。
响应 save_path 仍是 `/synthetic/service/...`，与本地 main 路径不同。
HTTP 请求中的 MUSIC method 是 callAPI_to_fileList，随后正文用流式下载读取。

## 已有目标与默认覆盖

重复调用并设置 overwrite=False，第一项已存在，返回 -10004 并停止。
仍请求了一次清单，但没有再次请求正文，也没有修改已有内容：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSDownloadError

calls_before = len(transport.calls)
protected = client.callAPI_to_downFile(
    interface_id, params, file_dir=output_root / "main", overwrite=False,
)
try:
    protected.raise_for_error(interface_id=interface_id, params=params)
except CMADaaSDownloadError as error:
    print(type(error).__name__, error.error_code, error.server_message)
else:
    raise AssertionError("existing target must fail when overwrite=False")
print("新增请求：", len(transport.calls) - calls_before)
print("已有内容：", [path.read_bytes() for path in paths])
```

下面主动将一个本地文件改成 LOCAL，再省略 overwrite，验证实际默认值 True。
正文重新下载，已有目标被替换：

```{code-cell} ipython3
paths[0].write_bytes(b"LOCAL")
overwritten = client.callAPI_to_downFile(interface_id, params, file_dir=output_root / "main")
overwritten.raise_for_error(interface_id=interface_id, params=params)
{"ok": overwritten.ok, "contents": [path.read_bytes() for path in paths]}
```

每个文件先写同目录临时 `.part` 文件，成功后替换目标；失败会清理该临时文件。
若 HTTP Content-Length 存在，会核对已写字节数；客户端没有用 FileInfo.size 校验正文，
也没有本地总字节或文件数量上限。示例另外核对实际文件大小与内容。

## 批量失败不回滚已写文件

单文件替换不代表整批事务。另建目标目录，只预置第二项为 KEEP；
第一项会下载成功，第二项因 overwrite=False 失败，已写第一项仍在磁盘：

```{code-cell} ipython3
partial_dir = output_root / "partial"
partial_dir.mkdir()
(partial_dir / "second.bin").write_bytes(b"KEEP")
calls_before = len(transport.calls)
partial = client.callAPI_to_downFile(interface_id, params, file_dir=partial_dir, overwrite=False)
try:
    partial.raise_for_error(interface_id=interface_id, params=params)
except CMADaaSDownloadError as error:
    print("ok:", partial.ok, type(error).__name__, error.error_code)
else:
    raise AssertionError("second existing target must stop the batch")
print("返回清单项数：", len(partial.files_info), "新增请求：", len(transport.calls) - calls_before)
print([(path.relative_to(output_root).as_posix(), path.read_bytes())
       for path in sorted(partial_dir.iterdir())])
```

失败 FilesInfo 仍含完整两项清单，不能把清单项数当作已完成下载数。
partial/first.bin 是 FAKE，partial/second.bin 仍是 KEEP；新增请求为清单加第一项正文。
业务需要按实际文件和状态决定重试/清理，不依据 save_path 或清单长度判断完成。

## 空清单与服务失败

```{code-cell} ipython3
empty_params = {**params, "dataCode": "SYNTHETIC_EMPTY"}
empty = client.callAPI_to_downFile(interface_id, empty_params, output_root / "empty", overwrite=False)
empty.raise_for_error(interface_id=interface_id, params=empty_params)
{"ok": empty.ok, "files_info": empty.files_info, "directory_created": (output_root / "empty").exists()}
```

成功空清单不创建目录或文件；错误码为零，与以下服务失败不同：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSRequestError

failed_params = {**params, "dataCode": "SYNTHETIC_ERROR"}
failed = client.callAPI_to_downFile(interface_id, failed_params, output_root / "failed", overwrite=False)
try:
    failed.raise_for_error(interface_id=interface_id, params=failed_params)
except CMADaaSRequestError as error:
    print("ok:", failed.ok, type(error).__name__, error.error_code, error.interface_id)
else:
    raise AssertionError("failed list must not download")
print("错误目标目录已创建：", (output_root / "failed").exists())
```

底层没有 strict 开关，下载后应检查 ok 或显式 raise_for_error。
处理过的清单、传输和下载错误记录在 request，本地配置/参数错误仍可能直接抛出。

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
check_download_results(
    {"preflight": preflight, "downloaded": downloaded, "protected": protected,
     "overwritten": overwritten, "partial": partial, "empty": empty, "failed": failed},
    output_root, transport, params,
)
```

```{code-cell} ipython3
workspace.cleanup()
print("临时文件已清理：", not output_root.exists())
```

## 已有在线记录与真实服务替换

LLF-002 于 2026-10-08 采用 GFS/TEM/103/动态三天前 06 时及 overwrite=False，
先用完全相同请求预查，受控下载一项 28,492,363 字节 GRIB2 并验证实际文件。
本次不重跑真实服务，两个小文件的人工结果不计新在线验证。

以下按同一查询最多一文件、已知大小合计不超过 32 MiB 预查，再下载到本地目录。
需真实 INI、账号与服务，**普通代码块不在文档构建时执行**：

```python
from pathlib import Path
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
infos = real_listing.files_info
if not 0 < len(infos) <= 1 or any(not info.size.isdecimal() or int(info.size) <= 0 for info in infos):
    raise RuntimeError("Expected one file with a known positive byte size")
if sum(int(info.size) for info in infos) > 32 * 1024 * 1024:
    raise RuntimeError("File preflight exceeds 32 MiB")

real_output_dir = Path("./cmadaas-native-files")
real_download = real_client.callAPI_to_downFile(
    real_interface_id, real_params, file_dir=real_output_dir, overwrite=False,
)
real_download.raise_for_error(interface_id=real_interface_id, params=real_params)
real_paths = [real_output_dir / info.file_name for info in real_download.files_info]
```

预查询与 downFile 会分别取得清单，服务内容期间可能变化；这个预查不保证下载阶段的
实时总字节上限。返回后仍需核对实际目录、名称、大小及文件格式，不能只凭 ok 或元数据
认定文件完整。使用独立目录便于处理已有目标和批量部分完成。
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，日期与案例见
{doc}`测试与动态时间 </development/testing>`，签名见
{doc}`客户端参考 </reference/client>`。

完整离线脚本从源码仓库根目录运行：

```bash
uv run python -m examples.music.files
```

脚本和本页共用 `examples/music/files.py` 的准备及磁盘断言。
下载流程实际执行七次清单、五次流式正文请求，核对响应关闭和临时文件清理，
无需配置或账号；正文与元数据清单查询分别验证。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。

## 完整案例索引

```{cmadaas-case-index}
```
