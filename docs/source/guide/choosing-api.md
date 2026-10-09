---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 选择高层业务 API 或底层 MUSIC 接口

高层函数适合按资料类别查询、转换和下载数据；底层 `CMADaaSClient.callAPI_to_*` 适合直接使用服务 interface、原生参数及响应对象。本页用同一个站点查询对照两种调用：获取两个站点的 `Station_Id_C,Lat,Lon,TEM` 表格。

本页使用人工合成数据，无需 CMADaaS 账号或配置。两个调用共用注入合成 transport 的真实 `CMADaaSClient`，都经过签名请求、protobuf 解码和表格转换；服务响应由本地辅助模块提供。数据准备与注入代码默认折叠，可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 如何选择

| 需要完成的工作 | 选择的入口 | 调用者负责的内容 |
| --- | --- | --- |
| 用日期、站号、区域、层次或时效查询常用资料 | {doc}`高层接口 <high-level/index>` | 选择公开函数及它支持的参数组合；函数选择已登记 interface 并转换结果 |
| 已知具体 MUSIC interface，或使用高层尚未封装的服务能力 | {doc}`底层 MUSIC 接口 <low-level/index>` | 按服务目录指定 interface、原生参数和匹配的返回方法，检查响应状态并转换 |
| 需要原始响应、文件清单、字符串或数据块 | {doc}`底层 MUSIC 接口 <low-level/index>` | 使用对应 `callAPI_to_*` 方法并处理其返回契约 |

高层仅支持当前登记的业务组合，未登记的组合会在请求前报 `UnsupportedQueryError`。底层接受调用者给出的 interface ID，但服务仍可能拒绝不存在的接口、不支持的返回形式或未授权的资料；不能据此认为它能查询任意数据。

## 同一任务的参数

`SYNTHETIC_STATION` 是虚构资料代码，`2026-01-02` 是固定合成时间。站号、坐标及 `TEM` 都是人工字符串值，`TEM` 的 `280.0`、`281.5` 不代表真实地面气温或单位。

| 高层参数 | 本例的值 | 底层 MUSIC 参数 |
| --- | --- | --- |
| `data_code` | `"SYNTHETIC_STATION"` | `dataCode` |
| `elements` | `"Station_Id_C,Lat,Lon,TEM"` | `elements` |
| `time` | `pd.Timestamp("2026-01-02")` | `times="20260102000000"` |
| `order` | 默认 `"Station_ID_d:asc"` | `orderby` |
| `client` | 已注入合成 transport 的客户端 | 使用该客户端直接调用方法 |
| `strict` | `True` | 响应对象调用 `raise_for_error()` |

这些映射针对本例的 `retrieve_obs_station()` 单时次查询；不同资料的时间键、要素键和 interface 可能不同。

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

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_synthetic_music_client,
)

transport = SyntheticTransport()
transport.register_api(
    "callAPI_to_array2D",
    "getSurfEleByTime",
    {
        "dataCode": "SYNTHETIC_STATION",
        "elements": "Station_Id_C,Lat,Lon,TEM",
        "orderby": "Station_ID_d:asc",
        "times": "20260102000000",
    },
    make_array2d_content(),
)
client = make_synthetic_music_client(transport)
```

## 高层：直接得到业务表格

高层函数接收 Python 时间对象，选择 `getSurfEleByTime` 并组装原生参数，成功时直接返回 DataFrame：

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

high_table = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    client=client,
    strict=True,
)
print(high_table.to_string(index=False))
```

## 底层：选择 interface 并转换响应

底层需要显式给出 interface、方法和原生参数。`callAPI_to_array2D()` 返回 `Array2D`，可读取 `request`、`element_names` 和 `data`；调用 `raise_for_error()` 后再通过 `to_pandas()` 得到表格：

```{code-cell} ipython3
interface_id = "getSurfEleByTime"
params = {
    "dataCode": "SYNTHETIC_STATION",
    "elements": "Station_Id_C,Lat,Lon,TEM",
    "times": "20260102000000",
    "orderby": "Station_ID_d:asc",
}
response = client.callAPI_to_array2D(interface_id, params)
response.raise_for_error(interface_id=interface_id, params=params)
low_table = response.to_pandas()
print(type(response).__name__, response.ok)
print(low_table.to_string(index=False))
```

两种调用都得到相同的两行表格，保留原始字符串列。高层把 interface 选择和转换封装在函数内；底层保留响应对象供调用者检查。转换结果还含 `attrs` 元数据，本例两条路径都包含相同的 `interface_id`、`request_time` 和 `response_time`。

```{code-cell} ipython3
:tags: [remove-cell]

from urllib.parse import parse_qs, urlsplit
from nuwe_cmadaas.music import Array2D, CMADaaSClient

assert isinstance(client, CMADaaSClient)
assert isinstance(response, Array2D)
pd.testing.assert_frame_equal(high_table, low_table)
assert high_table.values.tolist() == [
    ["FAKE001", "30.0", "110.0", "280.0"],
    ["FAKE002", "31.0", "111.0", "281.5"],
]
assert high_table.attrs == low_table.attrs
assert high_table.attrs["interface_id"] == "getSurfEleByTime"
assert high_table.attrs["request_time"] == "20260102000000"
assert high_table.attrs["response_time"] == "20260102000001"
assert len(transport.calls) == 2
for url, options in transport.calls:
    query = parse_qs(urlsplit(url).query)
    assert query["interfaceId"] == ["getSurfEleByTime"]
    assert query["method"] == ["callAPI_to_array2D"]
    assert query["dataCode"] == ["SYNTHETIC_STATION"]
    assert query["elements"] == ["Station_Id_C,Lat,Lon,TEM"]
    assert query["times"] == ["20260102000000"]
    assert query["orderby"] == ["Station_ID_d:asc"]
    assert options == {"timeout": (1, 1), "stream": True}
assert all(item.closed for item in transport.responses)
```

## 返回值与错误处理

高层成功返回 DataFrame、DataArray 或 `list[Path]`，具体由入口决定。默认 `strict=False` 时，服务错误返回 `MusicError`；使用 `strict=True` 时抛出结构化 `CMADaaSError`。查询参数非法或组合未支持属于请求前的本地错误。

底层 protobuf 方法返回响应对象，状态位于 `ok` 和 `request.error_code/error_message`。本例显式调用 `raise_for_error()` 采用异常控制流；也可先判断 `ok`。失败响应的 `to_pandas()` / `to_xarray()` 会抛异常，不能将转换失败当作空结果。`callAPI_to_serializedStr()` 返回字符串，错误字符串的兼容约定见 {doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。

未知或未登记的模拟请求会立即报 `AssertionError`，不会回退到网络。更换示例参数时须同步修改合成 transport 的登记内容。

## 切换到真实服务

高层可移除模拟 `client=`，用 `config=` 指定 CedarKit YAML；底层先用连接参数、配置字典或 MUSIC INI 创建真实客户端。也可以将这个真实客户端传给高层的 `client=`。两者的配置入口分别见 {doc}`高层配置 <configuration/high-level>` 与 {doc}`底层客户端配置 <configuration/music-client>`。

替换虚构资料代码、固定合成日期和站号后才可发起真实查询。真实资料必须支持对应 interface 和返回形式，时间按运行日期及资料类别选择，见 {doc}`测试与动态时间 </development/testing>`。本页合成结果只验证客户端调用路径，不证明账号权限或服务可用性。

## 按任务继续阅读

- {doc}`高层接口概览 <high-level/index>`：全部 8 个公开入口、通用参数及返回类型；按 {doc}`观测数据 <high-level/obs/index>` 或 {doc}`模式数据 <high-level/model/index>` 选择函数。
- {doc}`底层 MUSIC 接口概览 <low-level/index>`：全部 9 个方法、响应类型、转换与文件副作用。
- {doc}`高层 API 参考 </reference/high-level>` 与 {doc}`客户端参考 </reference/client>`：完整签名和参数说明。
