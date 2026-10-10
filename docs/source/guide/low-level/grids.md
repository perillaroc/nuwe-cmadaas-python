---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层格点：数组、标量与矢量

## 用途与示例来源

已知 MUSIC interface 和原生参数时，按服务支持的 protobuf 格式选择格点方法。
本页分别执行 gridArray2D、gridScalar2D 和 gridVector2D，展示原始数值、坐标、
名称和元数据，再调用 `to_xarray()`。业务层的预报/分析筛选见
{doc}`模式格点指南 </guide/high-level/model/grid>`。

| 方法 | 响应类型 | to_xarray() 结果 |
| --- | --- | --- |
| {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridArray2D` | GridArray2D | 二维 DataArray |
| {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridScalar2D` | GridScalar2D | 二维标量场 DataArray，不是单个数字 |
| {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridVector2D` | GridVector2D | 同一网格上含 U/V 两个变量的 Dataset |

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 `CMADaaSClient` 注入精确 `SyntheticTransport`，读取人工 protobuf，执行生产
解码和转换；未知请求立即失败，没有网络回退，不替换公开方法。
固定时次 `20260102060000`、SYNTHETIC 资料和要素、纬度 `[30,31]`、
经度 `[110,111,112]` 都用于离线演示。温度人工定义为 K；U/V 人工定义为 m/s，
但矢量响应及转换没有附加此单位，不能据此推断其他资料的单位或真实风值。

## 原生参数与准备

底层 `params` 使用接口要求的原生键，值按服务格式传入，不自动转换高层筛选，
也不执行高层登记组合校验。三个方法均不修改参数字典。

本页标量/数组查询使用以下原生参数：

- `interface_id`：`getNafpEleGridInRectByTimeAndLevelAndValidtime`。
- `dataCode`：`SYNTHETIC_GRID`；要素为 `fcstEle="synthetic_temperature"`。
- `time`：`"20260102060000"`，起报时次；`levelType="103"`、
  `fcstLevel="2"` 表示 2 米高度；`validTime="24"` 是预报小时数。
- 矩形：`minLat/maxLat="30.0"/"31.0"`，`minLon/maxLon="110.0"/"112.0"`。

本页矢量查询使用：

- `interface_id`：`getNafpVectorEleGridByTimeAndLevelAndValidtime`。
- `dataCode`：`SYNTHETIC_VECTOR`；要素使用小写原生键 **fcstuele** / **fcstvele**。
- `time` 与上方相同，但表示分析时次；`levelType="100"`、`fcstLevel="850"`
  表示 850 hPa，`validTime="0"` 表示分析资料的零时效。
- 本例接口未传矩形，不许诺同样的矩形参数可用。

两种查询都可选传 `server_id` 方法参数；省略则使用客户端节点，显式给出仅覆盖本次请求。

不要将 `forecast_time="24h"`、`region`、`parameter` 或 Timestamp 直接放进 params，
也不加入签名、userId、serviceNodeId 等封装字段，认证由客户端构造。
层次与时效意义依资料而定，不能把所有层次都当作气压或把 validTime 当绝对时间。

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

from examples.music.grids import make_grid_client, check_results

client, transport = make_grid_client()
```

(llg-001)=
## gridArray2D：一个二维 DataArray

调用先返回 `GridArray2D`，状态在 `request` 内；`ok` 只判断错误码是否为零。
本例行列计数来自人工响应，实际网格尺寸以 lat_count/lon_count 和坐标为准：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSClient

scalar_id = "getNafpEleGridInRectByTimeAndLevelAndValidtime"
scalar_params = {
    "dataCode": "SYNTHETIC_GRID", "fcstEle": "synthetic_temperature",
    "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "minLat": "30.0", "maxLat": "31.0",
    "minLon": "110.0", "maxLon": "112.0",
}
array_response = client.callAPI_to_gridArray2D(scalar_id, scalar_params)
{
    "response_type": type(array_response).__name__, "ok": array_response.ok,
    "error_code": array_response.request.error_code,
    "grid_shape": (array_response.lat_count, array_response.lon_count),
    "request_counts": (array_response.request.row_count, array_response.request.col_count),
}
```

```{code-cell} ipython3
{
    "data": array_response.data,
    "dtype": str(array_response.data.dtype),
    "latitude": array_response.lats, "longitude": array_response.lons,
    "name": array_response.user_element_name, "units": array_response.units,
}
```

protobuf 格点值已解码成浮点数，与底层 Array2D 表格的字符串不同。
六个固定值为 `[[280,280.5,281],[281.5,282,282.5]]`，本例名称为
synthetic_temperature、单位 K，均来自响应。

```{code-cell} ipython3
array_response.raise_for_error(interface_id=scalar_id, params=scalar_params)
array_field = array_response.to_xarray()
array_field
```

返回 `(latitude: 2, longitude: 3)`，维度顺序固定为 latitude、longitude。
纬度坐标附 `units="degrees_north"`，经度附 `units="degrees_east"`，两轴还有
standard_name/long_name。响应提供非空坐标数组时直接使用，保留其顺序；未提供时
按 start + index × step 和 count 生成，step 为零且 count 非零时用 start/end 等分。
转换不排序纬度、不倒置数值，也不重新插值；真实服务可返回降序坐标，应先检查。

```{code-cell} ipython3
{
    "dims": array_field.dims, "shape": array_field.shape,
    "latitude_attrs": array_field.latitude.attrs,
    "longitude_attrs": array_field.longitude.attrs,
    "attrs": array_field.attrs,
    "selected_temperature": array_field.sel(latitude=30.0, longitude=111.0).item(),
}
```

attrs 中 time 是原生起报字符串，valid_time 是 `"24"` 小时，level_type/level 是
`"103"/"2"`。它们是元数据，没有新增 time、valid_time、level 维度。
request_time/response_time 来自人工响应 `20260102000000/20260102000001`，
与起报时次独立，不表示真实耗时。dataCode、fcstEle、矩形边界不自动写入 attrs。
客户端也会附加可用的 timeRange/fcstMember 等通用字段，但不保证全部参数都有 attrs。

(llg-002)=
## gridScalar2D：标量场仍是二维 DataArray

用同一个已验证接口与参数改调用标量方法。本地工厂未提供显式坐标数组，
因此根据 start/step/count 生成相同的两条坐标。protobuf 的 datas 解码为响应的 data，
“Scalar” 表示每格一个标量，而不是只返回一个值：

```{code-cell} ipython3
scalar_response = client.callAPI_to_gridScalar2D(scalar_id, scalar_params)
scalar_response.raise_for_error(interface_id=scalar_id, params=scalar_params)
{
    "response_type": type(scalar_response).__name__, "ok": scalar_response.ok,
    "raw_data": scalar_response.data,
    "latitude": scalar_response.lats, "longitude": scalar_response.lons,
    "name": scalar_response.user_element_name, "units": scalar_response.units,
}
```

```{code-cell} ipython3
scalar_field = scalar_response.to_xarray()
scalar_field
```

```{code-cell} ipython3
{
    "result_type": type(scalar_field).__name__, "dtype": str(scalar_field.dtype),
    "dims": scalar_field.dims, "shape": scalar_field.shape,
    "attrs": scalar_field.attrs,
}
```

本例两个 DataArray 的坐标、数值、名称、单位和 metadata 相同，
但响应类及 protobuf 字段不同；不能据此断定所有 gridArray2D 接口都支持 gridScalar2D。
转换不自动识别缺测标记、不换算单位，真实资料需要按定义处理。

(llg-003)=
## gridVector2D：U/V 两个变量组成 Dataset

矢量接口使用 `fcstuele/fcstvele`，与标量的 fcstEle 不同。
本例模拟分析资料，850 hPa、零时效；不要直接复用上面的预报资料和 24 小时时效：

```{code-cell} ipython3
vector_id = "getNafpVectorEleGridByTimeAndLevelAndValidtime"
vector_params = {
    "dataCode": "SYNTHETIC_VECTOR", "fcstuele": "synthetic_u_wind",
    "fcstvele": "synthetic_v_wind", "time": "20260102060000",
    "levelType": "100", "fcstLevel": "850", "validTime": "0",
}
vector_response = client.callAPI_to_gridVector2D(vector_id, vector_params)
vector_response.raise_for_error(interface_id=vector_id, params=vector_params)
{
    "response_type": type(vector_response).__name__, "ok": vector_response.ok,
    "u_name": vector_response.u_element_name, "v_name": vector_response.v_element_name,
    "u_data": vector_response.u_datas, "v_data": vector_response.v_datas,
}
```

```{code-cell} ipython3
vector_field = vector_response.to_xarray()
vector_field
```

```{code-cell} ipython3
{
    "result_type": type(vector_field).__name__, "sizes": dict(vector_field.sizes),
    "variables": list(vector_field.data_vars),
    "u_values": vector_field["synthetic_u_wind"].values,
    "v_values": vector_field["synthetic_v_wind"].values,
    "dataset_attrs": vector_field.attrs,
    "component_attrs": {name: variable.attrs for name, variable in vector_field.data_vars.items()},
    "selected_v": vector_field["synthetic_v_wind"].sel(latitude=31.0, longitude=112.0).item(),
}
```

两个变量各为 `(2,3)`，U 为 `[[1,2,3],[4,5,6]]`，V 为其负值。
名称取响应 u_element_name/v_element_name，空名称分别回退 u/v；不强制重命名为 U/V。
Dataset.attrs 含 interface_id、time、level_type=`"100"`、level=`"850"`、
valid_time=`"0"` 和响应时间。当前每个变量 attrs 为空，Dataset.attrs 也无 units；
应先核实资料单位和分量定义，不能假设温度的单位规则适用于矢量。
转换不计算风速/风向、不旋转矢量、不自动掩膜缺测，也没有 component、time 或 level 维度。

## 空结果、服务错误与坏响应

三个方法的成功空响应都能转换，坐标长度均为零；矢量空 Dataset 仍保留两个变量。
下面实际发出三次已登记的空查询：

```{code-cell} ipython3
methods = [
    ("array", client.callAPI_to_gridArray2D, scalar_id, scalar_params),
    ("scalar", client.callAPI_to_gridScalar2D, scalar_id, scalar_params),
    ("vector", client.callAPI_to_gridVector2D, vector_id, vector_params),
]
empty_responses, empty_fields = {}, {}
for name, method, interface_id, params in methods:
    empty_params = {**params, "dataCode": "SYNTHETIC_EMPTY"}
    empty_responses[name] = method(interface_id, empty_params)
    empty_responses[name].raise_for_error(interface_id=interface_id, params=empty_params)
    empty_fields[name] = empty_responses[name].to_xarray()
    print(name, "ok:", empty_responses[name].ok, "sizes:", dict(empty_fields[name].sizes))
```

服务失败记录在 request 中，不接受 `strict=`；ok=False 与成功空结果不同。
显式 raise_for_error 传入查询上下文，失败 to_xarray 也会抛异常，不会当作空场：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSRequestError

failed_responses = {}
for name, method, interface_id, params in methods:
    failed_params = {**params, "dataCode": "SYNTHETIC_ERROR"}
    failed_responses[name] = method(interface_id, failed_params)
    try:
        failed_responses[name].raise_for_error(interface_id=interface_id, params=failed_params)
    except CMADaaSRequestError as error:
        print(name, "ok:", failed_responses[name].ok, type(error).__name__,
              error.error_code, error.interface_id)
    else:
        raise AssertionError("service failure must raise")
    try:
        failed_responses[name].to_xarray()
    except CMADaaSRequestError as error:
        print(name, "failed conversion:", error.error_code, "interface_id:", error.interface_id)
    else:
        raise AssertionError("failed grids must not convert")
```

转换内部的检查未传查询上下文，异常 interface_id 为 None；此前显式调用不会把
上下文存回响应。其他错误及底层状态说明见 {doc}`底层表格 <tables>`。
本地配置/参数错误仍可能直接抛出，不承诺所有失败都包装成响应对象。

坐标长度、网格尺寸和分量长度需要一致。人工坏矢量只给五个 V 值，
无法填满 2×3，生产解码记录 -10003 并保留 ValueError 原因链：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSDecodeError

malformed_params = {**vector_params, "dataCode": "SYNTHETIC_MALFORMED"}
malformed_response = client.callAPI_to_gridVector2D(vector_id, malformed_params)
try:
    malformed_response.raise_for_error(interface_id=vector_id, params=malformed_params)
except CMADaaSDecodeError as error:
    print("ok:", malformed_response.ok, type(error).__name__, error.error_code,
          "cause:", type(error.cause).__name__)
else:
    raise AssertionError("bad vector must fail decoding")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
check_results(
    {"array": array_response, "scalar": scalar_response, "vector": vector_response,
     **{f"empty_{name}": response for name, response in empty_responses.items()},
     **{f"failed_{name}": response for name, response in failed_responses.items()},
     "malformed_vector": malformed_response},
    {"array": array_field, "scalar": scalar_field, "vector": vector_field,
     **{f"empty_{name}": field for name, field in empty_fields.items()}},
    transport, scalar_params, vector_params,
)
```

## 已验证的服务组合与真实替换

以下是 2026-10-08 已有在线记录，本次不重跑，也不把人工数据计为新服务通过：

| 案例 | 方法与资料/查询 | 已有真实结果 |
| --- | --- | --- |
| LLG-001 | gridArray2D；GFS 预报 `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE`，TEM，103/2 米，24 小时，115–116°E / 39–40°N | 9×9 DataArray |
| LLG-002 | gridScalar2D；与 LLG-001 相同 | 9×9 DataArray |
| LLG-003 | gridVector2D；GFS 分析 `NAFP_ANA_FTM_GRAPES_GFS_NEHE`，WIU/WIV，100/850 hPa，零时效 | 720×1441 Dataset，变量 WIU_100/WIV_100 |

2026-10-07 的目录对这些接口只标注 gridArray2D/RetGridArray2D，而上述具体资料与
方法组合经实测可用；不要把目录标签或单次合成解码扩展成所有返回格式都支持。
最初以分析资料和 24 小时时效请求曾返回 -9002/-3001，不能据此宣称同组合可用。
真实矩形边界可能吸附到网格中心，应按返回坐标与网格间距核对，不能强求完全等于
输入边界；转换本身不裁剪。矢量接口的已有案例为全域，规模超过一百万格点。

下面复用动态三天前 06 时与 MUSIC INI。需真实配置、账号及服务，
**普通代码块不在文档构建时执行**。先选小矩形验证数组/标量方法：

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
real_scalar_id = "getNafpEleGridInRectByTimeAndLevelAndValidtime"
real_scalar_params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"), "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "minLon": "115", "maxLon": "116", "minLat": "39", "maxLat": "40",
}
real_scalar_fields = {}
for name, method in [("array", real_client.callAPI_to_gridArray2D),
                     ("scalar", real_client.callAPI_to_gridScalar2D)]:
    response = method(real_scalar_id, real_scalar_params)
    response.raise_for_error(interface_id=real_scalar_id, params=real_scalar_params)
    if response.lat_count * response.lon_count > 10000:
        raise ValueError("Unexpected rectangle grid size")
    real_scalar_fields[name] = response.to_xarray()
```

确需全域矢量时，另换分析资料和两个要素；沿用上面的客户端和动态时次：

```python
real_vector_id = "getNafpVectorEleGridByTimeAndLevelAndValidtime"
real_vector_params = {
    "dataCode": "NAFP_ANA_FTM_GRAPES_GFS_NEHE", "fcstuele": "WIU", "fcstvele": "WIV",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"),
    "levelType": "100", "fcstLevel": "850", "validTime": "0",
}
real_vector_response = real_client.callAPI_to_gridVector2D(real_vector_id, real_vector_params)
real_vector_response.raise_for_error(interface_id=real_vector_id, params=real_vector_params)
if real_vector_response.lat_count * real_vector_response.lon_count > 2000000:
    raise ValueError("Unexpected vector grid size")
real_vector_field = real_vector_response.to_xarray()
```

这些格点数检查在响应已经读取后进行，不限制传输字节或替代服务端裁剪。
真实运行应另核对坐标、要素/单位、资料时间、层次和有限值，不能只检查 ok 或非空。
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，动态时间及案例见
{doc}`测试与动态时间 </development/testing>`，完整签名见
{doc}`客户端参考 </reference/client>`。两层调用选择见
{doc}`接口选择 </guide/choosing-api>`。

完整离线示例从源码仓库根目录运行：

```bash
uv run python -m examples.music.grids
```

脚本与指南共用 `examples/music/grids.py` 的准备和独立结果断言，验证三个主场、
三种成功空场、三种服务失败、一种坏矢量及十次响应关闭，无需配置或账号。

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。

## 完整案例索引

```{cmadaas-case-index}
```
