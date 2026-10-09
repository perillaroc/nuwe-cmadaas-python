---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层表格：Array2D 到 DataFrame

## 用途与示例来源

已知 MUSIC interface ID 和服务参数时，用
{py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_array2D` 获取表格响应。
本页从原生点预报查询开始，展示 `Array2D` 的请求状态、列名、原始字符串数组，
再用 `to_pandas()` 转为 DataFrame。只需业务筛选时，可先读
{doc}`模式点指南 </guide/high-level/model/point>` 或
{doc}`接口选择 </guide/choosing-api>`。

本页使用人工合成数据，无需账号。准备代码默认折叠，可展开查看；详见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_TABLE`、`synthetic_temperature`、固定时次和两个位置均用于离线演示，
人工温度按 K 定义，不代表真实资料或单位。真实 `CMADaaSClient` 经注入的
`SyntheticTransport` 读取人工 protobuf，运行生产解码和转换；未知请求立即失败，
没有网络回退，也不替换公开方法。

## 原生参数与准备

此接口使用以下原生键和值。底层不会将高层 `start_time`、`forecast_time` 或
`point` 自动转为这些字段，也不套用高层接口登记的查询条件校验。
具体必需字段、取值、行数和要素由服务接口及资料定义决定。

| 参数 | 本例值与含义 |
| --- | --- |
| interface_id | `getNafpEleAtPointByTimeAndLevelAndValidtime`，必须支持 RetArray2D |
| dataCode / fcstEle | `SYNTHETIC_TABLE` / `synthetic_temperature`，资料和要素 |
| time | `"20260102060000"`，起报时次，不是绝对有效时间 |
| levelType / fcstLevel | `"103"` / `"2"`，本例表示 2 米高度，不能一律视为 hPa |
| validTime | `"24"`，整数预报小时数；这里不传 `"24h"` 或 Timedelta |
| latLons | `"30.0/110.0,31.0/111.0"`，每点按纬度/经度排列 |
| server_id | 可选方法参数，覆盖本次服务节点；省略则使用客户端配置 |

`params` 不放 `userId`、签名、`serviceNodeId` 等请求封装字段，客户端负责构造。
本方法不修改参数字典，不接受高层 `client=` 或 `strict=` 参数。

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

from examples.music.tables import make_table_client, check_results

client, transport = make_table_client()
```

## 发起请求，先检查状态

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSClient

interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
params = {
    "dataCode": "SYNTHETIC_TABLE",
    "fcstEle": "synthetic_temperature",
    "time": "20260102060000",
    "levelType": "103",
    "fcstLevel": "2",
    "validTime": "24",
    "latLons": "30.0/110.0,31.0/111.0",
}
response = client.callAPI_to_array2D(interface_id, params)
{
    "response_type": type(response).__name__,
    "ok": response.ok,
    "error_code": response.request.error_code,
    "error_message": response.request.error_message,
    "rows": response.request.row_count,
    "columns": response.request.col_count,
    "request_time": response.request.request_time,
    "response_time": response.request.response_time,
}
```

成功返回 `Array2D`，本例 `ok=True`、错误码 0、两行六列。
`ok` 只依据错误码是否为零，不代表结果非空或已通过气象质量检查。
`request` 是响应内的 `RequestInfo`；时间来自响应，不是客户端对起报时间的改写。
辅助生成器还将 `request_elements/request_params` 写为 `synthetic_elements/synthetic_params`，
`take_time` 保留默认 0，均是人工占位，不能当作输入参数回显或真实耗时。
真实服务可能在请求摘要中包含业务信息，不应将完整摘要、认证 URL 或凭据直接写入日志。

## 列名与原始二维数组

```{code-cell} ipython3
response.element_names
```

```{code-cell} ipython3
response.data
```

```{code-cell} ipython3
{
    "shape": response.data.shape,
    "dtype": str(response.data.dtype),
    "first_value_type": type(response.data[0, 0]).__name__,
    "row_count": response.row_count,
    "col_count": response.col_count,
}
```

这里是 `(2, 6)` 的 NumPy 字符串数组，两行分别为位置 `(30,110)` 和 `(31,111)`，
温度值为 `"280.0"/"281.5"`。`lat/lon/datetime/level/validtime` 和
`synthetic_temperature_103` 均是响应列名，不由客户端重命名；字段大小写和层次后缀
可能随接口变化。数组的行/列表示记录和字段，不能当作 latitude/longitude 格点维度，
也不保证真实服务总按输入点顺序返回完整记录。

## 转为表格并显式转换数值

```{code-cell} ipython3
import pandas as pd

response.raise_for_error(interface_id=interface_id, params=params)
table = response.to_pandas()
table
```

成功时 `raise_for_error()` 返回响应自身；失败时抛结构化异常。
先显式提供 interface 和参数，便于错误保留查询上下文。
`to_pandas()` 保留响应列名、值和顺序，不自动转换数值、日期、缺测或单位：

```{code-cell} ipython3
{
    "dtypes": table.dtypes.astype(str).to_dict(),
    "value_types": {column: type(table[column].iloc[0]).__name__ for column in table.columns},
    "attrs": table.attrs,
}
```

pandas 版本可能显示 `str` 或 `object`；实际值保持 Python 字符串。
attrs 含 interface_id、原生 time、level_type、level 和 valid_time，以及响应的
request_time/response_time。这里 `valid_time="24"` 仍是预报小时数，
没有新增时效或层次维度；dataCode、fcstEle、latLons 和 units 不自动写入 attrs。
本方法的通用 metadata 也可记录 timeRange、fcstMember 等对应字段，
但不自动记录所有参数；`minVT/maxVT` 等需调用方另行保存。

```{code-cell} ipython3
converted = table.copy()
converted["synthetic_temperature_103"] = pd.to_numeric(
    converted["synthetic_temperature_103"], errors="raise",
)
{
    "numeric_values": converted["synthetic_temperature_103"].tolist(),
    "numeric_dtype": str(converted["synthetic_temperature_103"].dtype),
    "original_values": table["synthetic_temperature_103"].tolist(),
}
```

副本得到 `[280.0, 281.5]`，原表仍为字符串。真实缺测标记应按资料定义先处理，
再决定转换失败策略；日期可用明确格式 `pd.to_datetime(..., format="%Y%m%d%H%M%S")`。

## 成功空结果与失败响应

人工空响应保留六列，错误码仍为零，转换后得到 `(0, 6)` 的空 DataFrame：

```{code-cell} ipython3
empty_params = {**params, "dataCode": "SYNTHETIC_EMPTY"}
empty_response = client.callAPI_to_array2D(interface_id, empty_params)
empty_response.raise_for_error(interface_id=interface_id, params=empty_params)
empty_table = empty_response.to_pandas()
{
    "ok": empty_response.ok,
    "raw_shape": empty_response.data.shape,
    "table_shape": empty_table.shape,
    "columns": empty_table.columns.tolist(),
    "empty": empty_table.empty,
}
```

服务业务错误由底层方法返回在响应中，没有 `strict` 开关；不要仅根据原始数组
是否为空判断成功。用 `raise_for_error()` 显式抛出异常：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSRequestError

failed_params = {**params, "dataCode": "SYNTHETIC_ERROR"}
failed_response = client.callAPI_to_array2D(interface_id, failed_params)
print("ok:", failed_response.ok, "code:", failed_response.request.error_code)
try:
    failed_response.raise_for_error(interface_id=interface_id, params=failed_params)
except CMADaaSRequestError as error:
    print(type(error).__name__, error.error_code, error.server_message, error.interface_id)
else:
    raise AssertionError("service failure must raise")
```

失败转换也会抛异常，不会返回一个看似成功的空表。转换内部未传查询上下文，
因此下面的异常 interface_id 为 None；此前调用 `raise_for_error()` 不会把上下文
存回响应。需要上下文时采用上面的显式检查：

```{code-cell} ipython3
try:
    failed_response.to_pandas()
except CMADaaSRequestError as error:
    print("failed conversion:", type(error).__name__, error.error_code,
          "interface_id:", error.interface_id)
else:
    raise AssertionError("failed response must not convert")
```

人工坏响应声明三行六列，却只有两行数据。生产解码会记录 `-10003`，
并保留导致失败的 ValueError；服务成功码也不能绕过结构检查：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSDecodeError

malformed_params = {**params, "dataCode": "SYNTHETIC_MALFORMED"}
malformed_response = client.callAPI_to_array2D(interface_id, malformed_params)
try:
    malformed_response.raise_for_error(interface_id=interface_id, params=malformed_params)
except CMADaaSDecodeError as error:
    print("ok:", malformed_response.ok, type(error).__name__, error.error_code,
          "cause:", type(error.cause).__name__)
else:
    raise AssertionError("malformed response must fail decoding")
```

连接处理的传输异常记录为 `-10001`，认证、其他业务错误按错误码转为相应异常。
本地配置、方法参数或请求构造错误仍可能直接抛出，不承诺所有异常都返回 Array2D。
合成演示不测试真实权限、服务可达性或资料可用性。

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
check_results(
    {"success": response, "empty": empty_response, "failed": failed_response,
     "malformed": malformed_response},
    table, converted, transport, params,
)
```

(llt-001)=
## 对应接口与真实服务替换

| 返回形式 | interface 与案例 | 能力边界 |
| --- | --- | --- |
| Array2D | `getNafpEleAtPointByTimeAndLevelAndValidtime`，LLT-001 | 点、起报时次、层次、单时效；要素及资料由服务定义 |

LLT-001 在 2026-10-08 使用 GFS 资料 `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE`、TEM、
103/2 米层次、24 小时时效及北京单点通过；真实列为
`lat/lon/datetime/level/validtime/TEM_103`，返回一行。本页两个人工点不扩充这条
在线记录，也不把离线成功计为新服务验证。历史停运的 MESO 10KM 不作为新示例。
方法可接受 interface ID 不等于该接口/资料/账号支持 RetArray2D；格点和文件响应
应使用对应方法，不能只靠更换方法名改变返回类型。

下面保留既有动态三天前 06 时规则。需要真实账号、配置和服务，**不在文档构建时执行**：

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
real_params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"),
    "levelType": "103", "fcstLevel": "2", "validTime": "24",
    "latLons": "39.9/116.4",
}
real_response = real_client.callAPI_to_array2D(
    "getNafpEleAtPointByTimeAndLevelAndValidtime", real_params,
)
real_response.raise_for_error(
    interface_id="getNafpEleAtPointByTimeAndLevelAndValidtime", params=real_params,
)
real_table = real_response.to_pandas()
```

真实运行还应核对返回位置、起报时次、层次、时效、字段和数值，而非只检查非空。
INI 与认证配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，
动态日期与案例登记见 {doc}`测试与动态时间 </development/testing>`。
签名及契约见 {doc}`客户端参考 </reference/client>` 和
{doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。

完整离线脚本在源码仓库根目录运行：

```bash
uv run python -m examples.music.tables
```

指南与脚本共用 `examples/music/tables.py` 的准备工厂和独立结果校验；
运行验证四次精确请求、真实解码/转换及响应关闭，无需配置或账号。
