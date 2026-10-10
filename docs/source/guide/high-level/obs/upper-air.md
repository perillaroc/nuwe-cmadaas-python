---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 高空观测数据

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.obs.retrieve_obs_upper_air` 获取高空观测表格。
常规定时值、GPS/MET、雷电定位（Light）和飞机观测（Ard）使用不同接口与字段，
不能只换资料代码就假定所有站点、区域、层次组合都可用。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_*` 资料代码、`FAKE001/FAKE002`、固定的 `2026-01-02` 和所有数值都属
离线演示，不是真实探空、GPS、雷电或飞机观测，也不代表各字段的实际单位。

准备代码注入 `SyntheticTransport`，按精确请求登记各分支的合成 protobuf；
公开调用经过真实 MUSIC 客户端、`Array2D` 解码和 `to_pandas()` 转换。
响应预先构造，不会根据任意层次、站号或区域动态过滤，未知请求直接失败。

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

from examples.high_level.upper_air import make_upper_air_client, check_results

client, transport = make_upper_air_client()
```

(ou-002)=
## 常规观测：按时次读取表格

`elements` 显式选择原始字段。单时次用 `pd.Timestamp` 或标准库 `datetime`，
映射为 `times`；时间列表同样生成 `times`，时间段用 `pd.Interval` 生成 `timeRange`。
普通查询的站点和层次筛选必须与已登记接口匹配。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_upper_air

regular_elements = "Station_Id_d,Lat,Lon,PRS_HWC,GPH,EVSS,TEM"
regular = retrieve_obs_upper_air(
    "SYNTHETIC_UPPER",
    elements=regular_elements,
    time=pd.Timestamp("2026-01-02"),
    client=client,
    strict=True,
)
regular
```

本例返回两行七列，底层选择 `getUparEleByTime`。
常规资料的 `Station_Id_d` 是站点字段，`PRS_HWC`、`GPH`、`EVSS` 分别用于本页
气压、高度、垂直特征层示例；`TEM` 是要素字段。列名、拼写和字符串值保留响应原样。
真实资料的字段解释、单位、缺测及质量标记应按该资料定义处理，不能沿用地面站点
`Station_Id_C` 的固定 schema。

```{code-cell} ipython3
print(regular.dtypes)
regular.attrs
```

所有值都是字符串；dtype 随 pandas 版本可能显示为 `object` 或字符串 dtype。
计算前按资料说明显式使用 `pd.to_numeric` 并处理缺测。`attrs` 包含 `interface_id`、
`request_time`、`response_time`；时间段分支另带 `time_range`。
当前 `times`、`pLayers/hLayers/verticals` 不自动写成 `attrs` 的时间或层次字段，
也不创建时间/层次索引，逐行层次应从实际返回列读取。

(ou-017)=
## 单站与气压层

`level_type` 与 `level` 必须一起提供。`pl` 映射为 `pLayers`，
下面的两层列表生成 `pLayers="850,700"`；单站生成 `staIds="FAKE001"`。
数量限制 `count=2` 映射为 `limitCnt`，这里限制的是记录数。

```{code-cell} ipython3
pressure = retrieve_obs_upper_air(
    "SYNTHETIC_UPPER",
    elements=regular_elements,
    time=pd.Timestamp("2026-01-02"),
    station="FAKE001",
    level_type="pl",
    level=[850, 700],
    count=2,
    client=client,
    strict=True,
)
pressure
```

该组合选择 `getUparEleByTimeAndStaIDAndPress`，合成结果两行都属于 `FAKE001`，
`PRS_HWC` 为字符串 `850/700`。多层数据仍是平面 DataFrame，不自动转成三维数组。
站点列表用 `list`；站号元组表示范围，但当前高空登记没有站号范围接口，
不能把 `station=("FAKE001", "FAKE002")` 当作两站列表。

(ou-015)=
(ou-016)=
### 高度与垂直特征层

`gh` 和 `hgt` 都生成 `hLayers`；`vertical` 生成 `verticals`。
两种查询仍通过同一个公开入口，但选择不同的层次接口：

```{code-cell} ipython3
height = retrieve_obs_upper_air(
    "SYNTHETIC_UPPER", elements=regular_elements,
    time=pd.Timestamp("2026-01-02"),
    level_type="gh", level=1500, client=client, strict=True,
)
vertical = retrieve_obs_upper_air(
    "SYNTHETIC_UPPER", elements=regular_elements,
    time=pd.Timestamp("2026-01-02"),
    level_type="vertical", level=4096, client=client, strict=True,
)
print(height.to_string(index=False))
vertical
```

此处分别选择 `getUparEleByTimeAndHeight` 与 `getUparEleByTimeAndVertical`。
对应合成列 `GPH=1500`、`EVSS=4096` 只是约定示例值，实际单位和编码按资料解释。
不能由层次类型注解推断所有层次范围、多个层次类型或站点组合都存在。

(oug-010)=
## GPS/MET：显式资料分支与站点参数

`interface_data_type="UparGps"` 选择 GPS family，不是任意资料类型字符串。
已内置资料的配置也可以自动指定分支；虚构资料在这里显式指定。

```{code-cell} ipython3
gps = retrieve_obs_upper_air(
    "SYNTHETIC_GPS",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    station="FAKE001",
    interface_data_type="UparGps",
    client=client,
    strict=True,
)
gps
```

返回本分支的 `Station_Id_C,Lat,Lon,TEM` 四列，不要求常规资料的 `PRS_HWC/GPH/EVSS`。
该请求选择 `getUparGpsEleByTimeAndStaID`。本库按已有接口参数契约移除其 `dataCode`；
`getUparGpsEleInRectByTime` 也会移除。高层仍接收 `data_code` 用于资料配置，
省略传输字段不能绕过账号权限。

(oug-011)=
### GPS 时间段接口保留 dataCode

时间段加站号选择 `getUparGpsEleByTimeRangeAndStaID`，该接口保留 `dataCode`。
这是三个已登记 GPS 接口之间的差异，不能统一省略所有 GPS 请求的资料代码。

```{code-cell} ipython3
window = pd.Interval(
    pd.Timestamp("2026-01-02"),
    pd.Timestamp("2026-01-02 01:00"),
    closed="left",
)
gps_range = retrieve_obs_upper_air(
    "SYNTHETIC_GPS",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=window,
    station="FAKE001",
    interface_data_type="UparGps",
    client=client,
    strict=True,
)
gps_range
```

`window` 包含左端零时、排除右端一时，原生值为
`timeRange="[20260102000000,20260102010000)"`。
合成响应只有一个固定站点行；真实多时次结果应请求资料支持的时间字段逐行区分。

(oul-009)=
## 雷电定位：矩形与时间段

`interface_data_type="UparLight"` 当前只有矩形加时间段组合。
雷电事件表不要求站号或探空气压层字段；这里显式请求 `Datetime,Lat,Lon`。

```{code-cell} ipython3
light = retrieve_obs_upper_air(
    "SYNTHETIC_LIGHT",
    elements="Datetime,Lat,Lon",
    time=window,
    region={
        "type": "rect",
        "start_longitude": 110,
        "end_longitude": 111,
        "start_latitude": 30,
        "end_latitude": 31,
    },
    interface_data_type="UparLight",
    client=client,
    strict=True,
)
light
```

该请求选择 `getUparLightEleInRectByTimeRange`。示例只有一条人工事件，
`Datetime=20260102003000` 位于请求窗口内；并未模拟真实雷电统计或完整字段集合。

(oua-001)=
## 飞机观测：时间段与飞行高度范围

`level_type="fl"`（实现也接受 `"flight_height"`）自动选择 Ard family。
当前只登记时间段加飞行高度范围，另可加矩形；单时次、单一飞行高度没有对应接口。
`level` 使用 `pd.Interval`，端点映射为 `minFLayer/maxFLayer`。

```{code-cell} ipython3
ard = retrieve_obs_upper_air(
    "SYNTHETIC_ARD",
    elements="Lat,Lon,Flight_Heigh,TEM",
    time=window,
    level_type="fl",
    level=pd.Interval(5000, 10000, closed="both"),
    client=client,
    strict=True,
)
ard
```

底层选择 `getUparArdEleByTimeRangeAndHeightRange`，合成两行的 `Flight_Heigh` 为
字符串 `6000/9000`。保留真实字段拼写 `Flight_Heigh`，不自动改成 `Flight_Height`。
高度范围只传两个数值端点，没有传 `pd.Interval.closed`；不能据此承诺服务的闭开边界。
固定合成数据验证本地请求和转换，不证明实际资料满足高度过滤或有可用观测。

(oulat-001)=
## latest：独立的最新时次表

相对时长使用非负整数小时的 `pd.Timedelta` 或标准库 `timedelta`。
latest 只接受资料代码和相对 `time`（客户端、配置及严格模式仍可设置），
选择高空自己的 `getUparLatestTime`，不复用地面 latest 接口。

```{code-cell} ipython3
latest = retrieve_obs_upper_air(
    "SYNTHETIC_UPPER",
    time=pd.Timedelta(hours=6),
    client=client,
    strict=True,
)
latest
```

合成响应是一行、单列 `Datetime`。已有高空真实服务记录也证实该时次字段，
本页没有重跑在线请求。latest 不读取普通要素配置，返回 schema 与上面四类观测表不同。
显式要素、层次、站号、区域、排序、数量、资料分支和额外 MUSIC 参数都在请求前拒绝。
取得时次后，应发起独立普通查询读取观测值，不能把 latest 表格当作文件清单。

## 参数与当前登记范围

| 参数 | 使用方式与边界 |
| --- | --- |
| `elements` | 逗号分隔字段；省略时读取内置高空资料配置，虚构/未登记代码应显式提供，否则可能 `KeyError` |
| `time` | 时次/列表生成 `times`，时间段生成 `timeRange`，相对时长生成 latest 请求；仍需匹配分支组合 |
| `station` | 单站字符串/整数或非空站号列表生成 `staIds`；元组范围没有已登记的高空接口 |
| `level_type` + `level` | 成对提供；`pl` → `pLayers`，`gh/hgt` → `hLayers`，`vertical` → `verticals`，`fl/flight_height` 自动切到 Ard |
| `region` | 已登记区域形式是矩形；行政区/流域组合在请求前拒绝 |
| `station_level` | 参数可规范化为 `staLevels`，但没有专用的高空等级登记；不能据签名宣称支持等级查询 |
| `order` | 映射为 `orderby`；当前内置资料的 `order_by` 会覆盖显式排序，须核对该资料配置 |
| `count` | 正整数，映射为 `limitCnt`；是否为所选 interface/资料支持的参数须另核对 |
| `interface_data_type` | 常规 `Upar`、GPS `UparGps`、雷电 `UparLight`、飞机 `UparArd`；省略时优先用内置资料配置，否则常规分支 |
| `config` / `client` | CedarKit YAML 路径或字典 / 已有客户端；显式 `client` 优先，见配置指南 |
| `strict` | 默认兼容 `MusicError`；`True` 时服务业务错误抛结构化 `CMADaaSError` |

当前登记 17 个组合，按分支整理如下；这不等于每个资料都支持这些接口：

| 分支 | 查询条件 | 对应 interface |
| --- | --- | --- |
| 常规 | 时次 / 时间段 | `getUparEleByTime` / `getUparEleByTimeRange` |
| 常规 | 矩形 + 时次/时间段 | `getUparEleInRectByTime` / `getUparEleInRectByTimeRange` |
| 常规 | 站号 + 时次/时间段 | `getUparEleByTimeAndStaID` / `getUparEleByTimeRangeAndStaID` |
| 常规 | 时次 + 气压/高度/垂直层 | `getUparEleByTimeAndPress` / `getUparEleByTimeAndHeight` / `getUparEleByTimeAndVertical` |
| 常规 | 时次 + 站号 + 气压层 | `getUparEleByTimeAndStaIDAndPress` |
| GPS | 矩形 + 时次；站号 + 时次；站号 + 时间段 | `getUparGpsEleInRectByTime`；`getUparGpsEleByTimeAndStaID`；`getUparGpsEleByTimeRangeAndStaID` |
| Light | 矩形 + 时间段 | `getUparLightEleInRectByTimeRange` |
| Ard | 时间段 + 飞行高度范围；再加矩形 | `getUparArdEleByTimeRangeAndHeightRange`；`getUparArdEleInRectByTimeRangeAndHeightRange` |
| latest | 仅资料代码与相对时长 | `getUparLatestTime` |

层次列表会以逗号连接；常规气压/高度/垂直层范围、多个层次类型组合、
高度或垂直层再加站号等没有相应登记。`level_type="flight_level"` 不是实现接受的别名。
类型注解或参数能被规范化，不等于存在服务接口；未登记组合在请求前抛 `UnsupportedQueryError`。

## 可复现的本地错误

下面分别演示缺少配对层次、未登记的飞机单高度查询和 latest 附加站号，
这些错误不发送传输请求：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

for label, selectors, error_type in [
    ("层次未配对", {"time": pd.Timestamp("2026-01-02"),
                   "elements": regular_elements, "level_type": "pl"}, ValueError),
    ("飞机单高度", {"time": pd.Timestamp("2026-01-02"),
                   "elements": regular_elements, "level_type": "fl", "level": 6000},
     UnsupportedQueryError),
    ("latest 附加站号", {"time": pd.Timedelta(hours=6), "station": "FAKE001"},
     UnsupportedQueryError),
]:
    calls_before = len(transport.calls)
    try:
        retrieve_obs_upper_air(
            "SYNTHETIC_UPPER", client=client, strict=True, **selectors,
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
    {"regular": regular, "pressure": pressure, "height": height, "vertical": vertical,
     "gps": gps, "gps_range": gps_range, "light": light, "ard": ard, "latest": latest},
    transport,
)
```

## 真实服务状态与替换方式

已有案例记录中，常规高空十个组合及高空 latest 有真实通过记录；GPS 三例与
Light 一例因资料权限返回 `-4001`，Ard 的两个案例分别遇到飞行高度缺测值 `999999`
和无记录，均不能记为有效观测验证成功。具体历史结果见仓库
`tests/integration/obs/upper/cases.yaml`；本任务不重跑在线请求或改变案例状态。
飞机合成值 `6000/9000` 不能替代真实有效高度的受控样本，权限、单位和缺测也需独立核对。

切换真实服务时替换资料、字段、站号和近期时间，并使用有效配置。
下面按现有常规资料配置查询单站气压层，采用运行日期三天前的时次；
该账号仍需相应资料权限和服务数据。以下代码需真实服务，不在文档构建时执行：

```python
retrieve_obs_upper_air(
    "UPAR_CHN_MUL_FTM",
    elements="Station_Id_d,Lat,Lon,PRS_HWC,GPH,EVSS,TEM",
    time=pd.Timestamp.now().normalize() - pd.Timedelta(days=3),
    station="YOUR_STATION_ID",
    level_type="pl",
    level=850,
    count=20,
    config="/path/to/cedarkit.yaml",
    strict=True,
)
```

配置规则见 {doc}`高层配置 </guide/configuration/high-level>`，日期规则见
{doc}`测试与动态时间 </development/testing>`，两层参数对照见
{doc}`接口选择 </guide/choosing-api>`。默认服务错误可能返回 `MusicError`，
应先检查类型再访问表格；严格模式的服务异常与参数/配置等本地异常分别处理。

## 取得并运行完整示例

共享源码为 `examples/high_level/upper_air.py`，本页复用客户端准备和结果断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.upper_air
```

脚本默认仅使用合成数据，展示九次查询的分支表格和 attrs，验证各自列名、
固定值及错误零请求；辅助代码不随 wheel 分发，不需要第二个示例安装包。
完整签名见 {py:func}`nuwe_cmadaas.obs.retrieve_obs_upper_air`；
表格处理可对照 {doc}`地面站点 <station>`，文件下载场景见 {doc}`文件下载 <files>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。

## 完整案例索引

```{cmadaas-case-index}
```
