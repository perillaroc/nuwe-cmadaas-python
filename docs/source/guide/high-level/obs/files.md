---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面观测文件下载

## 业务目的

用公开的 `download_obs_file()` 下载一个人工文件，并检查返回的路径与磁盘内容。临时目录在页面执行结束后清理。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 参数说明

`SYNTHETIC_STATION`、固定时次和 `.invalid` URL 只用于离线示例。文件清单描述 `synthetic.bin`，内容固定为 `b"FAKE"`，大小 4 字节。本例使用注入合成 transport 的真实 `CMADaaSClient`，让库完成解码和流式写文件。

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

from examples._support import (
    SyntheticTransport,
    make_file_bytes,
    make_files_info_content,
    make_synthetic_music_client,
)

transport = SyntheticTransport()
transport.register_api(
    "callAPI_to_fileList",
    "getSurfFileByTime",
    {"dataCode": "SYNTHETIC_STATION", "times": "20260102000000"},
    make_files_info_content(),
)
transport.register_download("https://synthetic.invalid/data.bin", make_file_bytes())
client = make_synthetic_music_client(transport)
directory = TemporaryDirectory()
```

## API 调用与返回结果

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import download_obs_file

paths = download_obs_file(
    "SYNTHETIC_STATION",
    time=pd.Timestamp("2026-01-02"),
    output_dir=directory.name,
    client=client,
    strict=True,
)
[(path.name, path.stat().st_size, path.read_bytes()) for path in paths]
```

公开函数返回 `list[Path]`。上面的输出只显示文件名、大小和内容，避免将临时目录的随机绝对路径写入文档。`FilesInfo` 是底层的文件清单响应，`Path` 才是高层下载后的文件位置。

```{code-cell} ipython3
:tags: [remove-cell]

assert len(paths) == 1
assert paths[0] == Path(directory.name) / "synthetic.bin"
assert paths[0].read_bytes() == b"FAKE"
assert len(transport.calls) == 2
assert all(response.closed for response in transport.responses)
directory.cleanup()
```

## 常见错误

模拟 transport 会拒绝任何未登记的 interface、参数或下载 URL。真实服务下载前应限定查询范围并检查文件清单的数量与大小。

## 对应底层 interface

本例使用 `getSurfFileByTime`。真实客户端先读取 `FilesInfo`，再从清单中的 URL 流式下载文件；签名请求沿用 `callAPI_to_fileList` 方法名，详见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 替换为真实服务

换成账号可访问的真实资料代码、近期时次和受控输出目录。高层 `config=` 使用 CedarKit YAML，或显式传入真实 `client=`。配置见 {doc}`配置介绍 </guide/configuration/index>`，在线文件时间规则见 {doc}`测试与动态时间 </development/testing>`。

## API reference

参见 {doc}`高层接口参考 </reference/high-level>`。
