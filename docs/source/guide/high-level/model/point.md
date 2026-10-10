---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 模式点与站点预报

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.model.retrieve_model_point` 查询指定经纬度或站号的模式预报。
成功返回 `pandas.DataFrame`，每行由服务响应中的位置、起报时间、层次、时效及要素
字段组成。本页演示单点、多点、点的时效范围，以及站号的单时效和范围。

`data_code/parameter` 选择资料与要素，`start_time` 是起报时次，`level_type/level`
配对指定层次；`forecast_time` 是单一时效或两个时效组成的元组。
`point` 按 **(纬度, 经度)** 顺序传坐标对，`station` 传站号；两者互斥且必须选择一个。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_MODEL_POINT`、`synthetic_temperature`、`FAKE001` 和固定起报时次
`2026-01-02 06:00` 仅用于离线演示。人工温度按 K 定义，但 Array2D 表格不自动给
每列附单位；不能从示例数值或列名推断其他真实资料的单位。

本例注入 `SyntheticTransport` 的真实 MUSIC 客户端，合成 protobuf 经生产解码和
`to_pandas()` 转换。未知请求立即失败，不回退网络；不替换高层函数，也不在本地
根据坐标或时效插值。每种响应提前登记，实际资料返回行数与字段仍由服务决定。

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

from examples.high_level.model_point import make_model_point_client, check_results

client, transport = make_model_point_client()
```

(mp-001)=
## 单点、单时效

下面查询纬度 30、经度 110 的 24 小时预报。层次类型 103、层次值 2 按服务约定
表示 2 米高度；与压力层不同，不能将所有 level 都视为 hPa。
字符串 `"24h"`、pandas Timedelta 或标准库 timedelta 都可表示单时效。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.model import retrieve_model_point

start_time = pd.Timestamp("2026-01-02 06:00")
point_table = retrieve_model_point(
    "SYNTHETIC_MODEL_POINT",
    parameter="synthetic_temperature",
    start_time=start_time,
    forecast_time="24h",
    level_type=103,
    level=2,
    point=(30.0, 110.0),
    client=client,
    strict=True,
)
point_table
```

选择 `getNafpEleAtPointByTimeAndLevelAndValidtime`，原生坐标为
`latLons="30.0/110.0"`，时效为 `validTime="24"`；返回一行六列。
真实插值方式和取值由服务决定，本库不实现格点到点的插值算法。

### 字段、dtype 与元数据

| 字段 | 本例含义与人工值 |
| --- | --- |
| `lat` / `lon` | 响应位置，`"30.0"` / `"110.0"` |
| `datetime` | 起报时次字符串 `"20260102060000"`，不是绝对预报有效时间 |
| `level` | 层次值字符串 `"2"`，单位由层次类型和资料定义 |
| `validtime` | 行内预报小时数字符串 `"24"` |
| `synthetic_temperature_103` | 人工要素值 `"280.0"`，本例按 K 定义 |

列名和大小写来自响应，不由高层重命名。这里返回列带层次后缀 `_103`，不等于
传入的 parameter；实际 GFS 案例返回 `TEM_103`，不能把所有资料都视为相同列集合。
所有单元格保持响应字符串，下面输出实际 dtype 和 Python 值类型：

```{code-cell} ipython3
{
    "dtypes": point_table.dtypes.astype(str).to_dict(),
    "value_types": {column: type(point_table[column].iloc[0]).__name__
                    for column in point_table.columns},
}
```

pandas 版本可能将字符串列显示为 `str` 或 `object`，都不表示自动数值化。

```{code-cell} ipython3
point_table.attrs
```

实际 attrs 包含 `interface_id`、请求 `time="20260102060000"`、
`level_type="103"`、`level="2"` 和单时效 `valid_time="24"`，后者是小时数，
不是绝对有效时间。`request_time/response_time` 来自合成响应，分别为
`20260102000000/20260102000001`，与起报时间独立，不能用来推断真实服务耗时。
本例 attrs 没有 units、latLons、staIds、资料代码或要素代码，业务需要时自行记录。

(mp-001-multi-point)=
## 多点列表

多点必须是非空坐标对列表，每项仍按纬度、经度排列。
列表生成 `latLons="30.0/110.0,31.0/111.0"`，复用单点接口：

```{code-cell} ipython3
multi_point = retrieve_model_point(
    "SYNTHETIC_MODEL_POINT", parameter="synthetic_temperature", start_time=start_time,
    forecast_time="24h", level_type=103, level=2,
    point=[(30.0, 110.0), (31.0, 111.0)], client=client, strict=True,
)
multi_point
```

人工响应返回两行，位置分别为 `(30,110)` 和 `(31,111)`，温度值为字符串
`"280.0"/"281.5"`。应核对返回位置和行数，不假定所有真实查询都按输入顺序逐点返回。

(mp-002)=
## 点的预报时效范围

范围用二元 **tuple** 表示，两个端点都是非负整数小时，起点不得大于终点。
它不是起报日期范围，不使用 pd.Interval，也不能用列表代替元组。

```{code-cell} ipython3
point_range = retrieve_model_point(
    "SYNTHETIC_MODEL_POINT", parameter="synthetic_temperature", start_time=start_time,
    forecast_time=("6h", pd.Timedelta(hours=24)), level_type=103, level=2,
    point=(30.0, 110.0), client=client, strict=True,
)
print(point_range.to_string(index=False))
print(point_range.attrs)
```

选择 `getNafpEleAtPointByTimeAndLevelAndValidtimeRange`，生成 `minVT="6"/maxVT="24"`。
人工响应含 6、12、24 小时三行，温度值为 `"276.0"/"278.0"/"280.0"`。
范围端点不决定输出步长，不能承诺每个整数小时均有记录；没有独立的区间闭合参数。

范围查询 attrs 保留 time、level_type、level 等元数据，但当前不自动保存
minVT/maxVT，也没有单时效 valid_time 或自动生成的 valid_time_range。
时效应读取每行 `validtime`；查询范围需业务代码另外保存。

### 显式转换数值并计算有效时间

在副本中转换，保留原表格字符串。这里按人工 datetime 格式解析起报时次，
加每行小时数形成明确的 `valid_at` 列；这不是库自动提供的坐标或字段。
真实 datetime 格式、时区及温度单位须另行核对，不能直接套用全部资料。

```{code-cell} ipython3
converted = point_range.copy()
for column in ["lat", "lon", "level", "validtime", "synthetic_temperature_103"]:
    converted[column] = pd.to_numeric(converted[column], errors="raise")
cycle = pd.to_datetime(converted["datetime"], format="%Y%m%d%H%M%S", errors="raise")
converted["valid_at"] = cycle + pd.to_timedelta(converted["validtime"], unit="h")
converted
```

三个有效时间为 `2026-01-02 12:00`、`2026-01-02 18:00`、`2026-01-03 06:00`。
`errors="raise"` 不会悄悄忽略非法字符串；资料缺测哨兵仍须按资料定义处理，
能转成数值并不代表有效观测或预报值。本例不自动换算温度单位。

(mp-003)=
## 站号的单时效

站号查询与坐标查询走不同接口，不同时传 point 和 station。
单站或非空站号列表生成 staIds；站号列表的服务支持须按具体资料核对。

```{code-cell} ipython3
station_table = retrieve_model_point(
    "SYNTHETIC_MODEL_POINT", parameter="synthetic_temperature", start_time=start_time,
    forecast_time=pd.Timedelta(hours=24), level_type=103, level=2,
    station="FAKE001", client=client, strict=True,
)
station_table
```

选择 `getNafpEleByTimeAndLevelAndValidtimeAndStaID`。
本例比点表格多一列 `station_id_c`，值为 `FAKE001`，温度值为 `"282.0"`。
该字段大小写与地面观测的 `Station_Id_C` 不同，以实际响应为准；站号保留字符串，
不要无故转成整数丢失前导零或非数字标识。

(mp-004)=
## 站号的时效范围

```{code-cell} ipython3
station_range = retrieve_model_point(
    "SYNTHETIC_MODEL_POINT", parameter="synthetic_temperature", start_time=start_time,
    forecast_time=("6h", "24h"), level_type=103, level=2,
    station="FAKE001", client=client, strict=True,
)
print(station_range.to_string(index=False))
print(station_range.attrs)
```

选择 `getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID`；三行均为 FAKE001，
时效 6、12、24，温度值 `"278.0"/"280.0"/"282.0"`。
站号元组被解释为站号范围，本入口不支持；不能用 `("FAKE001","FAKE002")`
表示两个独立站点，多个站点应使用列表。

## 成功空表格与服务错误

成功空响应可以产生零行表格，保留响应字段，不等于服务失败：

```{code-cell} ipython3
empty_table = retrieve_model_point(
    "SYNTHETIC_EMPTY", parameter="synthetic_temperature", start_time=start_time,
    forecast_time="24h", level_type=103, level=2, point=(30.0, 110.0),
    client=client, strict=True,
)
{"empty": empty_table.empty, "shape": empty_table.shape, "columns": empty_table.columns.tolist()}
```

真实服务也可能把无记录报为业务错误，不能把任何失败都当作空表格。
默认 strict=False 返回兼容的 MusicError，应检查返回类型后再使用表格。
strict=True 抛结构化 CMADaaSError；这里的 -4234 是人工错误码：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failed_code = None
try:
    retrieve_model_point(
        "SYNTHETIC_ERROR", parameter="synthetic_temperature", start_time=start_time,
        forecast_time="24h", level_type=103, level=2, point=(30.0, 110.0),
        client=client, strict=True,
    )
except CMADaaSError as error:
    failed_code = error.error_code
    print(type(error).__name__, error.error_code, error.interface_id)
else:
    raise AssertionError("service errors must raise in strict mode")
```

## 参数边界与对应底层接口

| 高层参数 | 服务参数及边界 |
| --- | --- |
| data_code / parameter | dataCode / fcstEle，必须匹配具体接口；字段名以响应为准 |
| start_time | pandas/标准库起报时次生成 time，不是绝对有效时间，也不支持 latest |
| forecast_time | 单时效生成 validTime；二元 tuple 范围生成 minVT/maxVT，均为整数小时 |
| level_type / level | 配对生成字符串 levelType/fcstLevel；服务层次代码，不自动映射 pl/gh 别名 |
| point | 纬度/经度元组或非空坐标对列表，生成 latLons；经纬度数值需有效 |
| station | 单站或非空列表生成 staIds；站号范围拒绝，与 point 互斥 |
| config / client | CedarKit 配置或 YAML 路径 / 已有客户端，显式 client 优先 |
| strict | 默认服务错误返回 MusicError；True 抛结构化异常，本地错误直接抛异常 |

本入口没有 data_type、number、region、count 或 `**kwargs`，不把格点的分析/成员/区域
参数或内部 feature 名 time/valid_time_range 传给此函数。当前只登记四种组合：

| 查询条件（均需起报时次和层次） | 底层 interface | 案例 |
| --- | --- | --- |
| 点 + 单时效 | `getNafpEleAtPointByTimeAndLevelAndValidtime` | MP-001/多点变体 |
| 点 + 时效范围 | `getNafpEleAtPointByTimeAndLevelAndValidtimeRange` | MP-002 |
| 站号 + 单时效 | `getNafpEleByTimeAndLevelAndValidtimeAndStaID` | MP-003 |
| 站号 + 时效范围 | `getNafpEleByTimeAndLevelAndValidtimeRangeAndStaID` | MP-004 |

底层均使用 callAPI_to_array2D，响应成功后转 to_pandas；这与格点 DataArray 的返回不同。
以下错误能离线复现，输出证明没有新增请求：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

default = {
    "data_code": "SYNTHETIC_MODEL_POINT", "parameter": "synthetic_temperature",
    "start_time": start_time, "forecast_time": "24h", "level_type": 103, "level": 2,
    "point": (30.0, 110.0), "client": client, "strict": True,
}
for label, selectors, error_type in [
    ("点与站号同时给出", {"station": "FAKE001"}, ValueError),
    ("缺少位置", {"point": None}, UnsupportedQueryError),
    ("经纬顺序颠倒且纬度越界", {"point": (110.0, 30.0)}, ValueError),
    ("空点列表", {"point": []}, ValueError),
    ("站号范围", {"point": None, "station": ("FAKE001", "FAKE002")}, TypeError),
    ("时效范围反向", {"forecast_time": ("24h", "6h")}, ValueError),
    ("时效范围误用列表", {"forecast_time": ["6h", "24h"]}, TypeError),
    ("非整数小时", {"forecast_time": "30min"}, ValueError),
    ("层次未配对", {"level": None}, ValueError),
]:
    calls_before = len(transport.calls)
    try:
        retrieve_model_point(**{**default, **selectors})
    except error_type:
        print(label, error_type.__name__, "是否发起请求：", len(transport.calls) != calls_before)
    else:
        raise AssertionError("invalid selectors must fail before a request")
```

颠倒经纬度后如果两个数值都在合法范围，库无法自动判断顺序错误，业务仍需核对位置。

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(
    {"point": point_table, "multi_point": multi_point, "point_range": point_range,
     "station": station_table, "station_range": station_range, "empty": empty_table},
    converted, transport, failed_code,
)
```

## 真实服务替换与完整示例

已有五个模式点案例在 2026-10-08 使用 GFS 资料
`NAFP_FOR_FTM_GRAPES_CFSV2_NEHE`、TEM、103/2 米层次和动态三天前 06 时通过；
坐标点/多点、站号 54511、单时效及 6–24 小时范围分别验证了位置、起报时次、层次、
时效与有限温度范围。本次不重跑在线验证，不将人工结果计为新服务通过。
历史低分辨率 MESO 10KM 资料已停运，不作为新示例；需要 MESO 时选目录支持的 3KM。

下面给出既有 GFS 坐标点案例的替换方式，日期使用原累计减三天 06 时规则。
仍需账号权限、资料可用时次和正确要素。此代码需真实服务，不在文档构建时执行：

```python
import pandas as pd
from nuwe_cmadaas.music import create_client
from nuwe_cmadaas.model import retrieve_model_point

real_client = create_client(config="/path/to/cedarkit.yaml")
recent_cycle = (
    (pd.Timestamp.now() - pd.offsets.Day()).normalize()
    - pd.Timedelta(days=2) + pd.Timedelta(hours=6)
)
table = retrieve_model_point(
    "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", parameter="TEM", start_time=recent_cycle,
    forecast_time="24h", level_type=103, level=2, point=(39.9, 116.4),
    client=real_client, strict=True,
)
```

替换为站号时移除 point，传 station="54511"；范围使用 forecast_time=("6h","24h")。
本入口没有 count，本页选择少点和短时效范围；实际仍应核对返回位置、记录数、字段和
资料定义，而不是只检查表格非空。配置见
{doc}`高层配置 </guide/configuration/high-level>`，动态日期规则见
{doc}`测试与动态时间 </development/testing>`，两层调用对照见
{doc}`接口选择 </guide/choosing-api>`。

共享源码为 `examples/high_level/model_point.py`，本页复用客户端准备和表格断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.model_point
```

脚本默认使用合成数据，执行五个查询、空表格、严格服务错误及九个零请求本地错误，
打印表格、dtype、attrs 和显式转换后的有效时间。无需账号或第二个示例安装包，
辅助模块不随 wheel 分发。完整签名见 {py:func}`nuwe_cmadaas.model.retrieve_model_point`；
二维场对照见 {doc}`模式格点 <grid>`，其他模式入口见 {doc}`模式目录 <index>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。

## 完整案例索引

```{cmadaas-case-index}
```
