---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层数据块：名称、bytes 与格式读取

## 用途与能力边界

{py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_dataBlock` 请求 RetDataBlock，
返回 DataBlock，由调用者检查状态并按已知格式读取 bytes。
`data_name` 是服务给出的名称字符串，`data` 是原始二进制内容；名称不是本地 Path，
方法不下载文件清单、不写磁盘，也没有自动文本解码或 pandas/xarray 转换。
查询文件元数据或下载文件时，见 {doc}`文件清单 <file-list>` 和 {doc}`文件下载 <downloads>`。

**当前没有已验证的真实 RetDataBlock 接口/资料组合。** 方法每次调用都会发出
`UserWarning: callAPI_to_dataBlock has no verified live-service interface`。
本页捕获并显示该警告，保持现有行为；合成结果只证明本地请求与解码流程。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 MUSIC 客户端经精确 SyntheticTransport 读取人工 protobuf，执行生产解码，
不替换公开方法；未知请求立即失败，没有网络回退。接口 `syntheticDataBlockByTime`、
资料代码和 NWB1 二进制格式均为虚构，**不是雷达、GRIB 或其他真实服务格式**。

## 原生参数

| 参数 | 本例与实际行为 |
| --- | --- |
| interface_id | 本例为虚构 `syntheticDataBlockByTime`；真实使用需确认 RetDataBlock 返回格式 |
| params | 本例原生 `dataCode`、`time`；真实键名由所选接口决定 |
| server_id | 可选节点，覆盖单次请求，省略使用客户端配置 |

不要传高层 parameter/start_time 等选择器；客户端负责签名和认证封装。
本方法不修改 params，没有 data_format、目标目录、overwrite 或 strict 参数。

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

from examples.music.data_block import make_data_block_client, check_data_block_results

client, transport = make_data_block_client()
```

## 调用与响应状态

临时空目录仅由本例创建，用来验证 API 没有写文件。

```{code-cell} ipython3
from tempfile import TemporaryDirectory
import warnings
from nuwe_cmadaas.music import CMADaaSClient, DataBlock

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
interface_id = "syntheticDataBlockByTime"
base = {"dataCode": "SYNTHETIC_BLOCK", "time": "20260102060000"}
queries = {"main": base.copy()}
results, errors, notices = {}, {}, []
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always", UserWarning)
    results["main"] = client.callAPI_to_dataBlock(interface_id, queries["main"])
notices.extend(str(item.message) for item in caught)
block = results["main"]
print("Warning:", notices[0])
print(type(block).__name__, "ok:", block.ok)
print("request:", vars(block.request))
print("metadata:", block.metadata)
block.raise_for_error(interface_id=interface_id, params=queries["main"])
```

ok 只表示 request.error_code 为零，不能证明内容非空或格式正确。
本例 request 的行列计数均为人工值 1，它们不是二维数组尺寸；data 是 bytes，
没有 element_names、latitude/longitude、units 或自动数值化。
metadata 在本例记录 interface_id/time，不将 bytes 转成带 attrs 的数据对象。

## 名称与非文本 bytes

```{code-cell} ipython3
print("data_name:", block.data_name, "type:", type(block.data_name).__name__)
print("data type:", type(block.data).__name__, "byte_count:", len(block.data))
print("raw:", repr(block.data))
print("hex:", block.data.hex())
print("files written:", [path.name for path in output_root.iterdir()])
```

得到 `synthetic_sample.bin` 和十字节 `4e5742310002fff900ff`。
名称虽有 .bin 后缀，仍只是元数据；客户端没有据此创建文件或选择读取器。
二进制中的 `00/ff` 原样保留，不做字符编码猜测。

## 按已知格式读取内存内容

本例格式明确约定为：4 字节 ASCII 签名 NWB1、两个大端整数（无符号 16 位计数、
有符号 16 位值）、2 字节尾标记 `00ff`。值没有气象单位或缺测含义。
先检查长度和签名，再用 BytesIO/struct 读取，不需要保存到文件：

```{code-cell} ipython3
from io import BytesIO
import struct

if len(block.data) != 10:
    raise ValueError("Unexpected synthetic byte count")
reader = BytesIO(block.data)
if reader.read(4) != b"NWB1":
    raise ValueError("Unexpected synthetic format signature")
count, signed_value = struct.unpack(">Hh", reader.read(4))
trailer = reader.read(2)
if trailer != b"\x00\xff" or reader.read(1) != b"":
    raise ValueError("Unexpected synthetic trailer")
parsed = {"count": count, "signed_value": signed_value, "trailer_hex": trailer.hex()}
parsed
```

计数为 2、有符号值为 -7；这是调用者按人工协议解析的字典，API 返回仍是 DataBlock。
真实内容应交给对应格式读取器，不使用此 NWB1 读取规则。
`len(data)` 是收到完整内容后的检查；客户端没有本地字节上限，不能将后检查当作传输限制。

## 文本与表格/格点转换边界

直接尝试 UTF-8 解码本例会失败。DataBlock 的 to_pandas/to_xarray 没有实现：

```{code-cell} ipython3
for name, operation in [
    ("utf8", lambda: block.data.decode("utf-8")),
    ("pandas", block.to_pandas), ("xarray", block.to_xarray),
]:
    try:
        operation()
    except (UnicodeDecodeError, NotImplementedError) as error:
        errors[name] = type(error).__name__
        print(name, errors[name])
```

这些转换错误不是服务请求失败，原响应仍然 ok。
不能对任意 bytes 默认调用 decode，也不能把数据块当成 Array2D/GridScalar2D 使用。

## 空成功、服务错误与解码错误

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always", UserWarning)
    for name, code in [
        ("empty", "SYNTHETIC_EMPTY"), ("service", "SYNTHETIC_ERROR"),
        ("decode", "SYNTHETIC_DECODE"),
    ]:
        queries[name] = {**base, "dataCode": code}
        results[name] = client.callAPI_to_dataBlock(interface_id, queries[name])
notices.extend(str(item.message) for item in caught)
for name in ["empty", "service", "decode"]:
    response = results[name]
    print(name, "ok:", response.ok, "error_code:", response.request.error_code,
          "name:", repr(response.data_name), "bytes:", repr(response.data))
    if not response.ok:
        try:
            response.raise_for_error(interface_id=interface_id, params=queries[name])
        except CMADaaSError as error:
            errors[name] = error
            print(type(error).__name__, "interface:", error.interface_id)
```

成功空响应为 `ok=True/data_name=""/data=b""`，不能当成非空数据块或在线支持证据。
服务失败 -10234 仍保留 `synthetic_failed.bin` 和 `b'\x00\xffERROR'`：
DataBlock 解码器不会因错误码非零就清空名称/bytes，**必须先检查状态再读取**。
坏 protobuf 返回 -10003 的失败响应，名称和内容保持默认空值。
raise_for_error 显式传 interface_id/params 才有这些错误上下文，底层没有 strict 开关。

```{code-cell} ipython3
:tags: [remove-cell]

check_data_block_results(results, queries, parsed, errors, notices, output_root, transport)
```

```{code-cell} ipython3
print("API requests:", len(transport.calls), "streamed file bodies:",
      sum(response.streamed for response in transport.responses))
print("all responses closed:", all(response.closed for response in transport.responses))
print("files written:", [path.name for path in output_root.iterdir()])
workspace.cleanup()
print("temporary directory removed:", not output_root.exists())
```

(llb-001)=
## LLB-001：服务待确认与真实客户端替换

独立登记案例 LLB-001 为 `implemented-unverified`、默认关闭；要求真实名称、非空 bytes
和受控大小。2026-10-07 核对的 413 个接口目录没有 RetDataBlock 标注。
名称含 DataBlock 的两个雷达接口实际标注 RetArray2D，且未列支持资料代码。
2026-10-08 用 RADA_L2_UFMT 探测 getRadaDataBlockByTime，目录方法返回 -2001
（资料未定义于接口），强行用 dataBlock 解码返回 -10003。
已通过的 GFS 点/格点接口强行解码可出现 ok=True 却名称/bytes 皆空，不能记为通过。
这些是既有核查记录，本页构建不重新访问服务，也不修改案例/profile 的关闭状态。

真实调用前需服务方确认 **返回 RetDataBlock 的接口 ID、账号授权的资料代码、
近期有数据且规模受控的样本时次，以及 payload 格式**。没有确认组合时保留待验证，
不要将 getRadaDataBlockByTime 直接视为可用数据块示例。
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`。

下列普通代码不在构建中执行。确认接口接受原生 dataCode/time 后设置三个环境变量；
样本时次须按该资料的更新频率、保留期和 UTC 格式选择，尚不能套用 GFS 的日期规则。
未配置时会在构造客户端与请求前拒绝。仅检查状态、名称、规模和前 16 字节，
不猜测真实格式、不使用人工 NWB1 解析器。

```python
import os
from datetime import datetime
from io import BytesIO
from nuwe_cmadaas.music import CMADaaSClient

interface_id = os.environ.get("CMADAAS_BLOCK_INTERFACE", "")
data_code = os.environ.get("CMADAAS_BLOCK_DATA_CODE", "")
sample_time = os.environ.get("CMADAAS_BLOCK_TIME", "")
if not interface_id or not data_code or not sample_time:
    raise ValueError("Confirm a RetDataBlock interface, authorized dataset and recent bounded sample first")
if len(sample_time) != 14 or not sample_time.isdigit():
    raise ValueError("Expected a confirmed UTC sample time in YYYYMMDDHHMMSS format")
datetime.strptime(sample_time, "%Y%m%d%H%M%S")

client = CMADaaSClient(
    config_file="client.config", user_id="YOUR_USER_ID", password="YOUR_PASSWORD",
    log_policy="redacted",
)
params = {"dataCode": data_code, "time": sample_time}
block = client.callAPI_to_dataBlock(interface_id, params)
block.raise_for_error(interface_id=interface_id, params=params)
if not block.data_name or not isinstance(block.data, bytes) or not 0 < len(block.data) <= 1024 * 1024:
    raise ValueError("Expected a named, nonempty block no larger than 1 MiB")
reader = BytesIO(block.data)
print(block.data_name, len(block.data), "prefix hex:", reader.read(16).hex())
```

1 MiB 是调用者的内容后检查，不限制传输内存；事先须选择已知受控样本。
构建和共享脚本使用的固定人工时次无需滚动更新；真实服务样本须另行确认。
本页没有新增真实服务成功记录。

## 独立运行与参考

在源码仓库根目录运行：

```bash
uv run python -m examples.music.data_block
```

脚本复用同一工厂，实际请求四种响应并独立核对名称、二进制字节、解析字段、
request/metadata、参数未修改、警告、错误上下文、响应关闭及无文件副作用。
指南的教学代码默认可见，准备可展开，独立结果断言不显示在教程中。
全部方法与兼容约定见 {doc}`底层 MUSIC 接口 <index>`、
{doc}`客户端参考 </reference/client>` 和 {doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。
