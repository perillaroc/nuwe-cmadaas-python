---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 模式格点数据

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.model.retrieve_model_grid` 获取一个模式预报或分析二维场。
成功返回 `xarray.DataArray`，维度为 `latitude/longitude`；本页分别执行全域、矩形、
集合成员和分析查询，展示实际坐标、数值、名称、单位及请求元数据。

`data_code` 选择资料，`parameter` 选择要素，`start_time` 表示起报时间或分析时次。
预报层次用 `level_type/level` 配对，`forecast_time` 表示单一预报时效；矩形用
`region`，成员用 `number`，分析场显式使用 `data_type="analysis"`。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_MODEL_GRID`、`synthetic_temperature` 和固定起报时间 `2026-01-02 06:00`
仅用于离线演示。温度值和单位 `K` 在合成响应中明确指定，不能外推真实资料的单位。

准备代码注入 `SyntheticTransport` 的真实 MUSIC 客户端。合成 protobuf 经生产解码和
`to_xarray()` 产生结果，不替换高层函数；八种查询各有精确登记，未知请求立即失败，
不回退真实网络。区域响应预先生成，不实现通用空间裁剪或动态模式计算。

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

from examples.high_level.model_grid import make_model_grid_client, check_results

client, transport = make_model_grid_client()
```

(mgf-008)=
## 一个起报时间、层次和时效的预报场

默认 `data_type` 为 `forecast`。本例 `level_type=100`、`level=850` 按服务层次约定
表示 850 hPa；其他层次类型应核对资料定义，不能把所有 level 都视为气压。
`forecast_time="24h"` 生成 `validTime="24"`，不是绝对有效时间字符串。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.model import retrieve_model_grid

start_time = pd.Timestamp("2026-01-02 06:00")
forecast = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID",
    parameter="synthetic_temperature",
    start_time=start_time,
    forecast_time="24h",
    level_type=100,
    level=850,
    client=client,
    strict=True,
)
forecast
```

该请求选择 `getNafpEleGridByTimeAndLevelAndValidtime`，经 `GridArray2D` 转换为
形状 `(2, 3)` 的 DataArray。`strict=True` 让服务错误直接抛结构化异常。

### 坐标、数值与本地索引

```{code-cell} ipython3
{
    "dimensions": forecast.dims,
    "latitude": forecast.latitude.values.tolist(),
    "longitude": forecast.longitude.values.tolist(),
    "latitude_units": forecast.latitude.attrs["units"],
    "longitude_units": forecast.longitude.attrs["units"],
}
```

纬度为 `[30.0, 31.0]`，经度为 `[110.0, 111.0, 112.0]`，单位分别为
`degrees_north/degrees_east`。真实网格方向和对齐以返回坐标为准，不假定总是递增。

```{code-cell} ipython3
forecast.values
```

第一行三个值为 `280.0/280.5/281.0`，第二行为 `281.5/282.0/282.5`；
格点值是浮点数，与表格保留字符串的行为不同。

```{code-cell} ipython3
{"name": forecast.name, "dtype": str(forecast.dtype), "attrs": forecast.attrs}
```

名称来自响应 `userEleName`，单位来自响应 `units`，不保证名称与请求要素相同。
库不自动完成单位换算或所有资料的缺测识别。本例实际 attrs 为：

| 字段 | 值与含义 |
| --- | --- |
| `units` | `K`，人工响应单位 |
| `interface_id` | 本次使用的具体 MUSIC 接口 |
| `time` | `20260102060000`，请求起报时间字符串 |
| `valid_time` | `"24"`，请求预报小时数，**不是绝对有效时间** |
| `level_type` / `level` | `"100"` / `"850"`，请求层次类型和值 |
| `request_time` / `response_time` | `20260102000000` / `20260102000001`，人工响应中的请求/响应时间 |

后两个时间用于说明响应 metadata，与上面的起报时次独立；它们是合成值，不能用来
判断真实服务耗时。结果没有 time、level、valid_time 或 member 维度。
当前 attrs 也不自动保存 data_code、parameter 或请求矩形，业务需要时自行记录。

```{code-cell} ipython3
forecast.sel(latitude=30.0, longitude=111.0).item()
```

精确选择已有格点得到 `280.5`，这是本地索引，不发新请求，也不进行插值。

(mgf-016)=
## 小矩形预报场

矩形需要四个经纬度端点。这里故意反向填写，规范化后生成
`minLat=30/maxLat=31/minLon=110/maxLon=111`。
时效也可以用 `pd.Timedelta` 或标准库 `timedelta` 表示，仍须为非负整数小时。

```{code-cell} ipython3
rectangle = {
    "type": "rect", "start_longitude": 111, "end_longitude": 110,
    "start_latitude": 31, "end_latitude": 30,
}
regional = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    forecast_time=pd.Timedelta(hours=24), level_type=100, level=850,
    region=rectangle, client=client, strict=True,
)
print(regional)
print(regional.values)
```

选择 `getNafpEleGridInRectByTimeAndLevelAndValidtime`，返回 `(2, 2)`，四个值为
`280.0/280.5/281.5/282.0`。请求端点不保证就是实际格点中心，分辨率及网格范围
须检查返回坐标；这里的合成矩形与全域对应位置一致，不能据此推断任意区域裁剪。

(mgf-017)=
## 集合控制成员

`number=None` 不添加成员参数；`number=0` 仍会发送 `fcstMember=0`，不会被当作未传。
成员编号与所用资料必须匹配。这里用虚构资料演示参数映射，实际 REPS 控制和扰动
资料使用不同资料代码，不能只改成员编号而忽略资料定义。

```{code-cell} ipython3
control = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    forecast_time="24h", level_type=100, level=850, number=0,
    client=client, strict=True,
)
print(control)
print(control.attrs)
```

选择 `getNafpEleGridByTimeAndLevelAndValidtimeAndFcstMember`。
结果仍为二维 `(2, 3)`，人工值为 `290.0` 到 `292.5`，attrs 新增整数 `member=0`。

(mgf-017-member-10)=
### 同一全域成员接口的既有变体

`MGF-017-member-10` 的在线记录以扰动资料 `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN`
和成员 10 调用同一全域接口；控制案例用 `NAFP_GRAPESREPS_FOR_FTM_CHN` 和成员 0。
两者既有通过记录不代表任意成员编号都可用，也不改变二维返回契约。

(mgf-018)=
## 矩形中的扰动成员

```{code-cell} ipython3
member = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    forecast_time="24h", level_type=100, level=850, number=10,
    region=rectangle, client=client, strict=True,
)
print(member)
print(member.values)
print(member.attrs)
```

选择 `getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember`，
返回 `(2, 2)`，四个人工值为 `300.0/300.5/301.5/302.0`，attrs 新增 `member=10`。
这个场与控制场数值独立，不是库根据编号计算出的扰动。

(mga-005)=
## 分析场必须省略预报时效

`data_type="analysis"` 选择分析接口族，`start_time` 此时是分析时次。
当前分析查询必须有时次和层次，**不传** `forecast_time` 和 `number`。
`forecast_time="0h"` 会增加时效筛选，不能替代省略；当前没有这种分析组合。

```{code-cell} ipython3
analysis = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    level_type=100, level=850, data_type="analysis", client=client, strict=True,
)
print(analysis)
print(analysis.attrs)
```

选择 `getNafpAnaEleGridByTimeAndLevel`，返回 `(2, 3)`，六个值从 `270.0` 到 `272.5`；
attrs 有 time、level_type、level，没有 valid_time 或 member。
分析资料也须逐接口匹配，不能把预报资料代码换 data_type 后直接认定可用。

(mga-013)=
### 矩形分析场

```{code-cell} ipython3
analysis_region = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    level_type=100, level=850, data_type="analysis", region=rectangle,
    client=client, strict=True,
)
print(analysis_region)
print(analysis_region.values)
```

选择 `getNafpAnaEleGridInRectByTimeAndLevel`，返回 `(2, 2)`，人工值为
`265.0/265.5/266.5/267.0`；没有自动添加时效或成员坐标。

(mgf-002)=
## 仅按起报时间的预报接口

这两个接口保留生产登记及离线映射，但真实案例曾以华南资料返回 `-3001` 要素配置
错误。按既有决定，`MGF-002/MGF-010` 均暂停在线验证，保留 `failed` 和
`needs-other-nafp-dataset`；本页合成成功不将它们改记为服务通过。
以下调用只证明当前高层路由和返回转换，不指定层次或时效：

```{code-cell} ipython3
time_only = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    client=client, strict=True,
)
print(time_only)
print(time_only.attrs)
```

选择 `getNafpEleGridByTime`，返回 `(2, 3)`，人工值从 `260.0` 到 `262.5`；
attrs 没有 level_type、level、valid_time、member。不能自行为返回场指定默认层次或时效。

(mgf-010)=
### 时次加矩形

```{code-cell} ipython3
time_only_region = retrieve_model_grid(
    "SYNTHETIC_MODEL_GRID", parameter="synthetic_temperature", start_time=start_time,
    region=rectangle, client=client, strict=True,
)
print(time_only_region)
print(time_only_region.values)
```

选择 `getNafpEleGridInRectByTime`，人工矩形为 `(2, 2)`，值为
`255.0/255.5/256.5/257.0`。若将来重启真实验证，需各接口目录支持的其他 NAFP
数值预报资料、已核实的要素、账号权限与近期时次，不继续猜测旧资料的要素名称。

## 参数与对应底层接口

| 高层参数 | 服务参数与边界 |
| --- | --- |
| `data_code` / `parameter` | `dataCode` / `fcstEle`；资料和要素须逐接口核对，不自动加载资料要素配置 |
| `start_time` | pandas/标准库时次生成 `time`；当前八个组合都要求明确时次 |
| `forecast_time` | 非负整数小时生成字符串 `validTime`；单一时效，不接受元组范围 |
| `level_type` / `level` | 配对生成字符串 `levelType` / `fcstLevel`；推荐服务定义的单层值 |
| `region` | None 全域或 rect 矩形；经纬端点校验并按 min/max 归一化 |
| `number` | `fcstMember`；本例 0/10 作为整数保存于 attrs，具体编号须匹配资料 |
| `data_type` | 默认 forecast；analysis 仅支持时次加层次及其矩形组合 |
| `config` / `client` | CedarKit YAML/配置对象或显式客户端；提供 client 后忽略 config |
| `strict` | 默认服务错误返回 MusicError；True 抛结构化异常 |

本函数没有 `**kwargs`，不接受内部 feature 名 `time/valid_time/valid_time_range` 作为
公开参数。层次类型直接转换为服务字符串，不使用高空表格的 pl/gh 别名映射。
本地通用 level 规范化并不承诺多层服务支持，当前教程只查询单层，不生成多层维度。

| 类型与查询条件 | 底层 interface | 案例 |
| --- | --- | --- |
| 预报：时次 | `getNafpEleGridByTime` | MGF-002 |
| 预报：时次 + 层次 + 时效 | `getNafpEleGridByTimeAndLevelAndValidtime` | MGF-008 |
| 预报：时次 + 矩形 | `getNafpEleGridInRectByTime` | MGF-010 |
| 预报：时次 + 层次 + 时效 + 矩形 | `getNafpEleGridInRectByTimeAndLevelAndValidtime` | MGF-016 |
| 预报：时次 + 层次 + 时效 + 成员 | `getNafpEleGridByTimeAndLevelAndValidtimeAndFcstMember` | MGF-017/成员 10 变体 |
| 预报：时次 + 层次 + 时效 + 成员 + 矩形 | `getNafpEleGridInRectByTimeAndLevelAndValidtimeAndFcstMember` | MGF-018 |
| 分析：时次 + 层次 | `getNafpAnaEleGridByTimeAndLevel` | MGA-005 |
| 分析：时次 + 层次 + 矩形 | `getNafpAnaEleGridInRectByTimeAndLevel` | MGA-013 |

所有组合使用 `callAPI_to_gridArray2D`，高层在响应成功后调用 `to_xarray()`。
未登记条件不能靠接口名拼接获得服务支持；高层不返回风矢量 Dataset。

## 服务错误与本地拒绝

默认 `strict=False` 的服务错误返回 `MusicError`，访问 `.values` 前应先检查类型。
严格模式抛 `CMADaaSError`，下面的 `-3234` 是合成错误码，独立于前述历史 `-3001`：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failed_code = None
try:
    retrieve_model_grid(
        "SYNTHETIC_ERROR", parameter="synthetic_temperature", start_time=start_time,
        forecast_time="24h", level_type=100, level=850, client=client, strict=True,
    )
except CMADaaSError as error:
    failed_code = error.error_code
    print(type(error).__name__, error.error_code, error.interface_id)
else:
    raise AssertionError("service errors must raise in strict mode")
```

本地非法参数和未登记组合直接抛异常，不转成 MusicError。比如没有起报时间、层次
只给一半、分析加时效、预报时效不带层次、时效范围、非整数小时、未知 data_type、
行政区查询，均在请求前拒绝：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

common = {
    "data_code": "SYNTHETIC_MODEL_GRID", "parameter": "synthetic_temperature",
    "start_time": start_time, "client": client, "strict": True,
}
for label, selectors, error_type in [
    ("缺少时次", {"start_time": None}, UnsupportedQueryError),
    ("层次未配对", {"level_type": 100}, ValueError),
    ("分析加零时效", {"data_type": "analysis", "level_type": 100, "level": 850,
                       "forecast_time": "0h"}, UnsupportedQueryError),
    ("时效缺层次", {"forecast_time": "24h"}, UnsupportedQueryError),
    ("时效范围", {"level_type": 100, "level": 850, "forecast_time": ("0h", "24h")}, TypeError),
    ("非整数小时", {"level_type": 100, "level": 850, "forecast_time": "30min"}, ValueError),
    ("未知类型", {"data_type": "bogus"}, ValueError),
    ("行政区", {"region": {"type": "region", "admin_codes": "110000"}}, UnsupportedQueryError),
]:
    calls_before = len(transport.calls)
    try:
        retrieve_model_grid(**{**common, **selectors})
    except error_type:
        print(label, error_type.__name__, "是否发起请求：", len(transport.calls) != calls_before)
    else:
        raise AssertionError("invalid selectors must fail before a request")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(
    {"forecast": forecast, "regional": regional, "control": control, "member": member,
     "analysis": analysis, "analysis_region": analysis_region,
     "time_only": time_only, "time_only_region": time_only_region},
    transport, failed_code,
)
```

## 真实服务替换与完整示例

真实调用需要同步替换资料、要素、层次、近期时次和客户端。后续优先使用各接口目录
支持的 GFS；MESO 选仍运行的 3KM 系统，不沿用已停运的低分辨率 10KM 资料。
已有模式格点记录中，MESO 3KM 预报/分析、REPS 控制/扰动的六种登记组合通过，
加全域成员 10 变体共七项正向通过；另外两种按时间查询保持历史失败和暂停状态。
这些是 2026-10-08 的记录，本次不重跑在线验证，也不外推其他资料或当前时次。

以下使用 B12 底层格点已验证的 GFS 资料、2 米 TEM 与相同矩形接口参数，
通过高层表达同一查询。日期按原累计减三天规则取 06 时，仍需实际账号权限和资料。
此代码需真实服务，不在文档构建时执行：

```python
import pandas as pd
from nuwe_cmadaas.music import create_client
from nuwe_cmadaas.model import retrieve_model_grid

real_client = create_client(config="/path/to/cedarkit.yaml")
recent_cycle = (
    (pd.Timestamp.now() - pd.offsets.Day()).normalize()
    - pd.Timedelta(days=2) + pd.Timedelta(hours=6)
)
field = retrieve_model_grid(
    "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", parameter="TEM", start_time=recent_cycle,
    forecast_time="24h", level_type=103, level=2,
    region={
        "type": "rect", "start_longitude": 115, "end_longitude": 116,
        "start_latitude": 39, "end_latitude": 40,
    },
    client=real_client, strict=True,
)
```

小区域限定查询范围，但不保证固定网格数；应核对返回坐标、单位和有限值。
分析或集合成员不能直接套用上面的预报资料，须选择具体接口支持的资料和参数。
配置见 {doc}`高层配置 </guide/configuration/high-level>`，日期规则见
{doc}`测试与动态时间 </development/testing>`，原生参数对照见
{doc}`接口选择 </guide/choosing-api>`。

共享源码为 `examples/high_level/model_grid.py`，本页复用其准备与结果断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.model_grid
```

脚本默认合成模式，执行八种登记查询，核对每个场的二维坐标、人工值、名称、单位及
完整 attrs，并验证服务异常与八种零请求本地错误。无需账号或第二个示例安装包，
辅助模块不随 wheel 分发。完整签名见 {py:func}`nuwe_cmadaas.model.retrieve_model_grid`，
其他模式入口见 {doc}`模式目录 <index>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。

## 完整案例索引

```{cmadaas-case-index}
```
