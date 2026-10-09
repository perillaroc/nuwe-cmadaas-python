---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面格点数据

## 业务目的与示例来源

用 {py:func}`~nuwe_cmadaas.obs.retrieve_obs_grid` 读取一个观测时次的格点场，
查看二维坐标、要素名称、单位和数值；需要限制空间范围时使用矩形 `region`。
成功返回 `xarray.DataArray`，维度为 `latitude/longitude`。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，
可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。
`SYNTHETIC_GRID`、`synthetic_temperature` 和固定时次 `2026-01-02` 仅用于离线演示。
本例六个温度值的单位明确设为 `K`，不能据此推断真实地面资料或降水要素的单位。

准备代码使用真实 MUSIC 客户端，HTTP 请求由 `SyntheticTransport` 截止，
合成 protobuf 经过生产解码和 `to_xarray()` 转换。全域与矩形响应分别预先登记，
模拟传输不会根据任意区域动态裁剪数据，未知请求立即失败。

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

from examples.high_level.grid import make_grid_client, check_results

client, transport = make_grid_client()
```

(og-002)=
## 查询一个观测时次

`data_code` 选择资料，`parameter` 指定该资料支持的要素代码，`time` 指定观测时次。
单时次映射为原生 `time="20260102000000"`，要素映射为 `fcstEle`。
这里不是模式起报时间或预报时效；`strict=True` 让服务业务错误直接抛异常。

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_grid

field = retrieve_obs_grid(
    "SYNTHETIC_GRID",
    parameter="synthetic_temperature",
    time=pd.Timestamp("2026-01-02"),
    client=client,
    strict=True,
)
field
```

该调用选择 `getSurfEleGridByTime`，底层返回 `GridArray2D`，高层转换为一个
`DataArray`。本例形状为 `(2, 3)`，第一轴是纬度，第二轴是经度。

## 二维坐标与六个数值

```{code-cell} ipython3
{
    "dimensions": field.dims,
    "latitude": field.latitude.values.tolist(),
    "longitude": field.longitude.values.tolist(),
    "latitude_units": field.latitude.attrs["units"],
    "longitude_units": field.longitude.attrs["units"],
}
```

纬度为 `[30.0, 31.0]`，经度为 `[110.0, 111.0, 112.0]`；坐标单位分别为
`degrees_north` 和 `degrees_east`。读取格点位置应使用返回的坐标，
不应仅根据请求边界自行生成坐标或假定真实资料纬度总是递增。

```{code-cell} ipython3
field.values
```

这里是二维浮点数组：第一行的 `280.0/280.5/281.0` 对应纬度 30，第二行的
`281.5/282.0/282.5` 对应纬度 31；每列按经度顺序排列。
格点值已是数值类型，与站点 DataFrame 保留原始字符串的行为不同。

### 要素名称、单位与请求元数据

```{code-cell} ipython3
{"name": field.name, "dtype": str(field.dtype), "attrs": field.attrs}
```

`field.name` 来自响应的 `userEleName`，`attrs["units"]` 来自响应的 `units`，
不保证名称一定与请求的 `parameter` 相同。示例输出为 `synthetic_temperature`、`K`。
库不会自动换算单位或识别所有资料的缺测标记；实际处理应依据资料定义及返回信息。

本例 `attrs` 还包含 `interface_id`、`time`、`request_time`、`response_time`。
`time` 是传给服务的观测时次字符串；后两者是合成响应的请求/响应时间，
不能当作额外的观测时间坐标。结果没有 `time` 维度，也没有预报时效或成员维度。

### 按坐标读取格点

```{code-cell} ipython3
field.sel(latitude=30.0, longitude=111.0).item()
```

此处精确选中已有格点，得到 `280.5`；这是返回数组上的本地索引操作，
不会发起新的服务请求，也不进行插值。

(og-005)=
## 查询一个矩形区域

`region` 需要四个经纬度端点。端点顺序会归一化：下面故意将起点写得比终点大，
最终发送 `minLat=30.0/maxLat=31.0`、`minLon=110.0/maxLon=111.0`。

```{code-cell} ipython3
regional = retrieve_obs_grid(
    "SYNTHETIC_GRID",
    parameter="synthetic_temperature",
    time=pd.Timestamp("2026-01-02"),
    region={
        "type": "rect",
        "start_longitude": 111,
        "end_longitude": 110,
        "start_latitude": 31,
        "end_latitude": 30,
    },
    client=client,
    strict=True,
)
regional
```

该调用选择 `getSurfEleGridInRectByTime`。预先登记的矩形响应形状为 `(2, 2)`，
纬度仍为 `[30.0, 31.0]`，经度为 `[110.0, 111.0]`，四个值如下：

```{code-cell} ipython3
regional.values
```

这四个合成值与全域场对应位置一致，但本例没有实现通用空间裁剪。
真实服务的网格范围及格点对齐以返回坐标为准，不能把请求矩形端点视作
精确的网格中心，也不能把这个小数组的大小当作真实资料分辨率。

## 参数与能力边界

| 参数 | 用法与当前行为 |
| --- | --- |
| `data_code` | 账号可访问且接口支持的资料代码；本例为虚构代码 |
| `parameter` | 要素字符串，映射为 `fcstEle`；建议显式指定，本函数不读取站点要素配置 |
| `time` | `pd.Timestamp` 或标准库 `datetime`；单时次映射为 `time` |
| `region` | `None` 表示全域；`type="rect"` 表示矩形，端点必须是有效经纬度数值 |
| `config` | CedarKit YAML 路径或配置字典；见高层配置指南 |
| `client` | 显式注入的客户端；提供后使用该客户端并忽略 `config` |
| `strict` | 默认 `False` 返回兼容的 `MusicError`；`True` 抛结构化服务异常 |
| `**kwargs` | 原样传给所选 MUSIC 接口的其他参数；是否支持须核对资料接口 |

当前只登记以下两类接口组合：

| 查询条件 | 底层 interface | 输出 |
| --- | --- | --- |
| 观测时次 | `getSurfEleGridByTime` | 二维 `DataArray` |
| 观测时次 + 矩形 | `getSurfEleGridInRectByTime` | 二维 `DataArray` |

本地时间规范化也接受非空时间列表/元组，将其映射为 `times` 并选择同一时次接口；
这只说明当前参数转换路径。是否接受多时次、如何返回由资料服务决定，
不能据此承诺时间维度、多个格点场或逐时拼接。本页只演示单时次。

虽然函数注解保留 `pd.Interval`，当前没有登记时间段或时间段加矩形接口；
省略时间、只传矩形也没有对应组合，均在请求前报 `UnsupportedQueryError`。
行政区和流域不是本入口的已登记区域形式。相对 `Timedelta` 会报 `TypeError`，
此入口不执行 latest 查询。

以下时间段错误可以离线复现；输出证明不会发起传输请求：

```{code-cell} ipython3
from nuwe_cmadaas.interfaces import UnsupportedQueryError

calls_before = len(transport.calls)
try:
    retrieve_obs_grid(
        "SYNTHETIC_GRID",
        parameter="synthetic_temperature",
        time=pd.Interval(
            pd.Timestamp("2026-01-02"),
            pd.Timestamp("2026-01-02 06:00"),
            closed="left",
        ),
        client=client,
        strict=True,
    )
except UnsupportedQueryError as error:
    print(type(error).__name__)
    print("是否发起请求：", len(transport.calls) != calls_before)
else:
    raise AssertionError("time-range queries must fail before a request")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert len(transport.calls) == calls_before
check_results(field, regional, transport)
```

## 常见错误与真实服务替换

服务业务错误在默认模式返回 `MusicError`，应先检查类型再访问 `.values`；
`strict=True` 则抛 `CMADaaSError`。非法类型或区域、缺失配置、不支持的组合等本地错误
直接抛异常，不转成 `MusicError`。更换本页参数后若遇到模拟路由错误，
应同步更新合成响应登记，不能让模拟传输回退真实网络。

真实调用需要替换资料、要素和近期时次，并使用账号有效的配置。
下面使用已有验证记录中的 CMPAS 降水资料与小矩形，时间按三天前动态计算；
仍需该账号的资料权限和服务数据。真实 `PRE` 单位以资料及返回结果为准，
不沿用上文合成温度的 `K`。以下代码需真实服务，不在文档构建时执行：

```python
field = retrieve_obs_grid(
    "SURF_CMPAS_CHN_1KM_RT",
    parameter="PRE",
    time=pd.Timestamp.now().normalize() - pd.Timedelta(days=3),
    region={
        "type": "rect",
        "start_longitude": 115,
        "end_longitude": 116,
        "start_latitude": 39,
        "end_latitude": 40,
    },
    config="/path/to/cedarkit.yaml",
    strict=True,
)
```

配置说明见 {doc}`高层配置 </guide/configuration/high-level>`，
真实资料的动态日期规则见 {doc}`测试与动态时间 </development/testing>`，
原生请求和高层调用的区别见 {doc}`接口选择 </guide/choosing-api>`。

## 取得并运行完整示例

共享源码为仓库中的 `examples/high_level/grid.py`，本页复用客户端准备和结果断言。
取得完整源码并安装主项目后，从仓库根目录运行：

```bash
uv run python -m examples.high_level.grid
```

脚本默认仅使用合成数据，输出全域和矩形数组、坐标、名称、单位、attrs，
验证两组结果及不支持查询的请求前拒绝；不读取账号配置。
示例辅助代码不随主包 wheel 分发，也不需要安装第二个示例包。
完整签名见 {py:func}`nuwe_cmadaas.obs.retrieve_obs_grid`；
表格结构可对照 {doc}`地面站点 <station>`，文件需求见 {doc}`文件下载 <files>`。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。
