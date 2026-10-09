---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面站点数据

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.obs.retrieve_obs_station` 获取地面站点观测表，
再按业务需要筛选、转换数值和处理缺测。普通查询返回 `pandas.DataFrame`；
相对时长的 latest 查询返回最新时次表，不能直接当作站点观测表使用。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_STATION`、`FAKE001/FAKE002` 和固定的 `2026-01-02` 都仅用于离线演示；
`TEM` 的 `280.0/281.5` 是人工字符串，不代表真实地面气温或其单位。

示例使用真实 MUSIC 客户端和 protobuf 解码、DataFrame 转换，HTTP 请求由
`SyntheticTransport` 截止。模拟响应预先登记，不会根据筛选参数计算新数据；
未知请求直接失败。这些结果证明本地调用和转换契约，不能证明真实资料的接口权限。

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

from examples.high_level.station import make_station_client, check_results

client, transport = make_station_client()
```

(os-002)=
## 查询一个时次

`data_code` 指定资料，`elements` 是逗号分隔的原始字段名，`time` 是观测时次。
自定义资料应显式指定 `elements`；省略时会读取内置 `station` 资料配置，未登记的
资料代码可能产生 `KeyError`。`strict=True` 让服务业务错误以异常形式中断调用。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

table = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    client=client,
    strict=True,
)
table
```

底层选择 `getSurfEleByTime`，发送 `times="20260102000000"`；返回的 `Array2D`
转换为两行四列表格，列名保留响应中的大小写。普通表格不自动设站号或时间索引，
也不自动转换数值、时间、单位或缺测编码。

## dtype、attrs 与数值转换

```{code-cell} ipython3
table.dtypes
```

四列的值都是字符串，dtype 随 pandas 版本可能显示为 `object` 或字符串 dtype。
站号应保留字符串，以免丢失前导零；计算 `TEM` 前明确转换：

```{code-cell} ipython3
numeric = table.copy()
numeric["TEM"] = pd.to_numeric(numeric["TEM"], errors="raise")
numeric[["Station_Id_C", "TEM"]]
```

`errors="raise"` 会暴露无法解析的值。真实资料的缺测编码和单位应先按该资料说明
识别，再替换缺测、转换数值；数字形式的缺测标记不能只靠 `errors="coerce"` 判断。
此处原始 `table` 保持字符串，不进行 Kelvin/摄氏度换算。

```{code-cell} ipython3
table.attrs
```

本例实际包含 `interface_id`、`request_time`、`response_time`。
后两者是合成响应的请求/响应时间字符串，不能当作每条观测的时次。
地面站点请求使用 `times`，当前不会将它自动写为 `attrs["time"]`；
时间段请求会附加 `time_range`。`attrs` 也不包含完整筛选条件、字段单位或质量标记。

(os-007)=
## 单站、站点列表与时间段

`station="FAKE001"` 表示单站，`count=1` 映射为服务参数 `limitCnt`，限制记录数：

```{code-cell} ipython3
single = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    station="FAKE001",
    count=1,
    client=client,
    strict=True,
)
single
```

(os-009)=
站点列表用 `list`，时间段用 `pd.Interval`。以下区间包含左端零时，排除右端六时，
原生请求为 `staIds="FAKE001,FAKE002"` 和
`timeRange="[20260102000000,20260102060000)"`。

```{code-cell} ipython3
selected = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Interval(
        pd.Timestamp("2026-01-02"),
        pd.Timestamp("2026-01-02 06:00"),
        closed="left",
    ),
    station=["FAKE001", "FAKE002"],
    client=client,
    strict=True,
)
selected
```

此处两行由合成响应给定，不意味着真实服务始终每站一行。
多时次或时间段查询应在 `elements` 中请求资料支持的时间字段（例如 `Datetime`），
逐行时次从该字段读取，不能用请求 `attrs` 替代。

(os-014)=
## 矩形与其他区域筛选

矩形的经纬度四个端点会归一化为最小/最大值，然后映射为
`minLat/maxLat/minLon/maxLon`。本例采用两个虚构站点所在的范围：

```{code-cell} ipython3
regional = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    region={
        "type": "rect",
        "start_longitude": 110,
        "end_longitude": 111,
        "start_latitude": 30,
        "end_latitude": 31,
    },
    client=client,
    strict=True,
)
regional
```

区域也可用 `{"type": "region", "admin_codes": "110000"}` 表示行政区，
或 `{"type": "basin", "basin_codes": "CJLY"}` 表示流域。
这些编码的实际支持由资料决定，不能与站号条件同时指定。

### 参数类型与已登记组合

| 参数 | 高层形式 | 原生参数或约束 |
| --- | --- | --- |
| `time` | `pd.Timestamp` / `datetime`；非空时间列表或元组 | `times`；多个时次逗号连接 |
| `time` | `pd.Interval` | `timeRange`；`closed` 控制端点包含关系 |
| `station` | 单站字符串/整数；非空站号列表 | `staIds`；推荐字符串保留前导零 |
| `station` | 两个站号组成的元组 | `minStaId/maxStaId`；表示范围，不能当作两个离散站号 |
| `station_level` | 字符串或非空字符串列表，如 `"011"`、`["011", "012"]` | `staLevels`；专用等级接口使用时间段，组合能力须核对资料 |
| `order` | 排序表达式，默认 `"Station_ID_d:asc"` | `orderby`；字段须在资料中可用，等级查询不发送排序 |
| `count` | 正整数，默认 `None` | `limitCnt`；不是所有资料/interface 都接受，例如已有等级案例不传此项 |
| `**kwargs` | 资料接口支持的 MUSIC 参数，如 `eleValueRanges` | 原样传递；不用于绕过高层组合约束 |
| `config` / `client` | CedarKit YAML 路径或字典 / 已有客户端 | 提供 `client` 时使用该客户端；见配置指南 |

当前普通站点接口登记支持以下组合；单时次和时间列表使用同一类时间接口：

| 查询条件 | 对应底层 interface |
| --- | --- |
| 时次 / 时间段 | `getSurfEleByTime` / `getSurfEleByTimeRange` |
| 时次或时间段 + 单站/站点列表 | `getSurfEleByTimeAndStaID` / `getSurfEleByTimeRangeAndStaID` |
| 时次或时间段 + 站号范围 | `getSurfEleByTimeAndStaIdRange` / `getSurfEleByTimeRangeAndStaIDRange` |
| 时间段 + 站点等级 | `getSurfEleByTimeRangeAndStaLevels` |
| 矩形 + 时次/时间段 | `getSurfEleInRectByTime` / `getSurfEleInRectByTimeRange` |
| 行政区 + 时次/时间段 | `getSurfEleInRegionByTime` / `getSurfEleInRegionByTimeRange` |
| 流域 + 时次/时间段 | `getSurfEleInBasinByTime` / `getSurfEleInBasinByTimeRange` |
| 单站/站点列表，不传时间 | `getSurfEleByStaID`；只用于该接口支持的资料，如气候值 |

这些是本库已登记的接口组合，不是每种资料的能力列表。未传任何时间/站号、
只传区域、只传站号范围、单时次加等级、区域加站号等组合会在请求前报
`UnsupportedQueryError`。接口存在也不能保证特定资料支持该接口和可选参数。
例如按站号查气候值与普通逐小时资料查询具有不同的资料和排序配置。
同时传入站号与等级时，当前实现按站号路由并附带 `staLevels`，不选择专用等级
接口；这不能证明服务支持二者组合，本指南不将其列为已确认能力。

(osl-001)=
## latest 返回最新时次，不返回站点要素

`time=pd.Timedelta(hours=6)`（也可用标准库 `timedelta`）表示相对查询窗口，
会选择 `getSurfLatestTime`，仅发送 `dataCode` 和 `latestTime="6"`。
相对时长必须是非负整数小时；字符串 `"6h"` 不属于此入口的 `time` 类型。

```{code-cell} ipython3
latest = retrieve_obs_station(
    "SYNTHETIC_STATION",
    time=pd.Timedelta(hours=6),
    client=client,
    strict=True,
)
latest
```

合成结果为一行、单列 `Datetime`，值为 `20260102000000`。
已有真实服务契约记录也证实该接口返回 `Datetime` 时次表；本页没有重跑在线请求。
它不包含 `Station_Id_C/Lat/Lon/TEM`，因此不能沿用普通表格的列检查。
取得真实时次后，应解析 `Datetime` 并发起独立的普通观测查询。

latest 不读取内置要素配置，也不接受显式 `elements`、站号、区域、等级、数量、
非默认排序或额外 MUSIC 参数；附加筛选会在请求前拒绝，不会被静默忽略：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

calls_before = len(transport.calls)
try:
    retrieve_obs_station(
        "SYNTHETIC_STATION",
        time=pd.Timedelta(hours=6),
        station="FAKE001",
        client=client,
        strict=True,
    )
except UnsupportedQueryError as error:
    print(type(error).__name__)
    print("是否发起请求：", len(transport.calls) != calls_before)
else:
    raise AssertionError("latest-time filters must fail before a request")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(table, single, selected, regional, latest, numeric, transport)
```

## 常见错误与真实服务替换

默认 `strict=False` 时，服务业务错误返回 `MusicError`，此时应先检查返回类型，
不要直接访问 `.columns`；`strict=True` 则抛结构化 `CMADaaSError`。
不支持的组合、非法时间/数量、资料配置缺失等本地错误直接抛异常，不会转成
`MusicError`。本页采用严格模式避免把服务失败当作空表；模拟客户端的未知路由
错误意味着示例登记与调用不一致。

切换真实服务时换成账号可访问的资料、要素和站号，并按运行日期计算时间。
以下代码需真实服务，在文档构建时不执行：

```python
retrieve_obs_station(
    "SURF_CHN_MUL_HOR",
    elements="Station_Id_C,Lat,Lon,TEM",
    station="YOUR_STATION_ID",
    time=pd.Timestamp.now().normalize() - pd.Timedelta(days=1),
    count=20,
    config="/path/to/cedarkit.yaml",
    strict=True,
)
```

配置查找和客户端优先级见 {doc}`高层配置 </guide/configuration/high-level>`；
真实资料的动态日期约定见 {doc}`测试与动态时间 </development/testing>`；
原生 MUSIC 参数对照见 {doc}`接口选择 </guide/choosing-api>`。

## 取得并运行完整示例

共享源码为仓库中的 `examples/high_level/station.py`，准备代码和结果断言与本页复用。
取得完整源码并安装主项目即可运行；该模块不随 wheel 分发，也不需要第二个示例安装包。
从仓库根目录执行：

```bash
uv run python -m examples.high_level.station
```

脚本默认只运行本页的合成查询，输出普通表格、筛选结果、latest、dtype 和 attrs，
并验证全部结果；不读取账号配置。函数完整签名见
{py:func}`nuwe_cmadaas.obs.retrieve_obs_station`，后续可阅读
{doc}`地面格点 <grid>` 或 {doc}`文件下载 <files>`。
