---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 使用返回结果：数值、单位、缺测与元数据

## 先确认返回类型与状态

高层成功结果主要是 DataFrame、二维 DataArray 或已下载的 `list[Path]`；
默认模式还可能返回 MusicError，应按 {doc}`错误处理 <errors>` 先检查结果。
底层 protobuf 响应要检查 ok/request，转换前显式 raise_for_error。

| 返回形式 | 读取与处理 |
| --- | --- |
| DataFrame / Array2D.to_pandas() | 保留字段名和字符串；计算前按资料定义数值化 |
| DataArray / 数组与标量格点.to_xarray() | latitude/longitude 二维坐标；值为数值，不自动换单位或屏蔽缺测 |
| 矢量格点.to_xarray() | U/V Dataset；不能假定分量有 units，见 {doc}`底层格点 <low-level/grids>` |
| 高层 list[Path] | 实际下载路径；检查存在、大小及内容，不是文件清单响应 |
| FilesInfo | 服务文件元数据；清单查询本身不写文件，size 为字符串、save_path 为服务路径 |
| DataBlock | 名称字符串与 bytes；按已确认格式读取，名称不是本地路径，无 pandas/xarray 转换 |
| serializedStr | 原始 str；自行检查业务状态并解析，没有 request/ok/attrs |

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
共享准备在 `examples/high_level/handling.py`，真实客户端经 SyntheticTransport
解码人工 protobuf 和流式写文件，不 mock 公开方法；未知请求立即失败，无网络回退。
**仅在本例定义**温度单位 K、缺测标记 999999，并故意加入非法字符串 bad。
这些不是 CMADaaS 通用单位/缺测约定；真实资料需核对要素说明、编码、比例因子及质量字段。

```{code-cell} ipython3
:tags: [hide-input]

import os
import sys
from pathlib import Path

start = Path(os.environ.get("NUWE_CMADAAS_REPO_ROOT", Path.cwd())).resolve()
repo_root = next(
    (path for path in (start, *start.parents)
     if (path / "examples" / "_support" / "synthetic.py").is_file()), None,
)
if repo_root is None:
    raise RuntimeError("Run this example from a nuwe-cmadaas-python checkout")
sys.path.insert(0, str(repo_root))
from examples.high_level.handling import make_results_client, check_results

client, transport = make_results_client()
```

(table-numbers)=
## 表格：保留原值，审计数值转换

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

time = pd.Timestamp("2026-01-02")
columns = "Station_Id_C,Lat,Lon,TEM"
table = retrieve_obs_station(
    "SYNTHETIC_RESULTS", elements=columns, time=time, client=client, strict=True,
)
print(table.to_string(index=False))
print("dtypes:", table.dtypes.to_dict())
print("attrs:", table.attrs)
```

站号作为标识字符串保留，避免丢失前导零；Lat/Lon 也没有自动数值化。
dtype 的显示名称随 pandas 版本变化，检查时应关注单元值仍是字符串。
先按资料定义屏蔽已知缺测，再尝试严格转换。这里的 bad 会使 errors="raise" 报错：

```{code-cell} ipython3
service_missing = table["TEM"].eq("999999")
masked = table["TEM"].mask(service_missing)
try:
    pd.to_numeric(masked, errors="raise")
except ValueError as error:
    print("strict numeric conversion:", type(error).__name__)

kelvin = pd.to_numeric(masked, errors="coerce")
invalid = masked.notna() & kelvin.isna()
print("known missing stations:", table.loc[service_missing, "Station_Id_C"].tolist())
print("invalid token stations:", table.loc[invalid, "Station_Id_C"].tolist())
```

errors="coerce" 是此处明确选择的策略：记录非法 token，再将它标为缺失；
不要把新增 NaN 静默当成服务缺测。客户端不会自动识别哨兵，也不提供通用质量控制。
在副本中转换单位，并显式记下处理含义：

```{code-cell} ipython3
cleaned = table.copy()
cleaned["TEM_C"] = kelvin - 273.15
cleaned.attrs = {
    **table.attrs, "TEM_C_units": "degC",
    "missing_policy": "synthetic 999999; invalid tokens audited",
}
print(cleaned[["Station_Id_C", "TEM", "TEM_C"]].to_string(index=False))
print("processed attrs:", cleaned.attrs)
```

280.0 K 对应约 6.85 °C，281.5 K 对应约 8.35 °C；原 TEM 字符串保留供核查。
TEM_C_units/missing_policy 是调用者增加的记录，不是服务提供的标准字段。
DataFrame.attrs 本身不含每列单位定义，不能从字段名 TEM 或本页的人工值推断真实单位。

(grid-units)=
## 格点：先屏蔽缺测，再转换单位

```{code-cell} ipython3
from nuwe_cmadaas.obs import retrieve_obs_grid

field = retrieve_obs_grid(
    "SYNTHETIC_RESULTS", parameter="synthetic_temperature", time=time,
    client=client, strict=True,
)
print(field)
print("dtype:", field.dtype, "attrs:", field.attrs)
print("coordinate units:", field.latitude.attrs, field.longitude.attrs)
```

原格点为 float32、2×3，999999 仍是普通数值；客户端不自动转成 NaN。
这个人工响应明确给出 units="K"，因此本例可转换为 °C：

```{code-cell} ipython3
if field.attrs.get("units") != "K":
    raise ValueError("This conversion requires confirmed Kelvin input")
celsius = (field.where(field != 999999.0) - 273.15).rename("synthetic_temperature_celsius")
celsius.attrs = {**field.attrs, "units": "degC", "missing_policy": "synthetic 999999"}
print(celsius)
print("processed attrs:", celsius.attrs)
```

单位判断只是本例的明确前提，不是单位解析器。真实资料若单位缺失、使用不同编码或
有缩放/质量标记，先查对应规范；不能硬套常量 273.15 或缺测值 999999。
运算后显式设置 attrs，避免依赖 pandas/xarray 某项操作是否保留属性。
原场和坐标顺序保持不变，无排序、插值或自动时次展开。

(result-metadata)=
## attrs 的来源与限制

| 来源 | 当前附加字段 |
| --- | --- |
| 客户端 | interface_id |
| 原生参数存在时 | time→time、timeRange→time_range、validTime→valid_time、levelType→level_type、fcstLevel→level、fcstMember→member |
| DataFrame/xarray 转换时的响应 | 非空 request_time、response_time（已有同名 metadata 优先） |
| 格点 payload | 数组/标量场的 units、名称与经纬度坐标；矢量分量单位不会自动补齐 |

不是所有请求都有所有 attrs；原生 times 不映射为 time，所以本页表格没有 time 属性。
request_time/response_time 是服务请求/响应元数据，不能直接当作观测时次。
dataCode、elements、latLons、区域边界以及完整查询参数不会自动全部写入 attrs，
应由调用者另存必要的查询记录。不要把认证信息写入处理记录。

```{code-cell} ipython3
print("table has time attr:", "time" in table.attrs)
print("grid dimensions:", field.dims, "coordinates:", list(field.coords))
print("grid time metadata:", field.attrs["time"])
print("grid has time dimension:", "time" in field.dims)
```

time/level/member attrs 是描述，不创建对应维度。合并多时次/层次/成员时，应核对
每次查询和坐标，再由调用者显式构造维度；attrs 也不承诺跨保存格式或所有运算自动保留。

(empty-results)=
## 合法空结果与文件路径

成功空表格仍有列，空格点 size=0；缺测满场与零大小场不是同一概念。
本例对明确的成功空响应使用 strict=True，也不会抛业务异常：

```{code-cell} ipython3
empty_table = retrieve_obs_station(
    "SYNTHETIC_EMPTY", elements=columns, time=time, client=client, strict=True,
)
empty_field = retrieve_obs_grid(
    "SYNTHETIC_EMPTY", parameter="synthetic_temperature", time=time, client=client, strict=True,
)
print("empty table:", empty_table.shape, "columns:", empty_table.columns.tolist(), "empty:", empty_table.empty)
print("empty grid:", empty_field.shape, "size:", empty_field.size)
```

真实服务若用非零错误码表示查询失败，按 {doc}`错误处理 <errors>` 处理，不能改称合法空结果。
业务承诺有数据的正向样本还需单独检查非空。

```{code-cell} ipython3
from tempfile import TemporaryDirectory
from nuwe_cmadaas.obs import download_obs_file

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
paths = download_obs_file(
    "SYNTHETIC_RESULTS", time=time, count=1, output_dir=output_root / "files",
    client=client, strict=True,
)
empty_paths = download_obs_file(
    "SYNTHETIC_EMPTY", time=time, count=1, output_dir=output_root / "empty",
    client=client, strict=True,
)
print("path list:", [(type(path).__name__, path.name, path.is_file(), path.stat().st_size, path.read_bytes())
                     for path in paths])
print("empty path list:", empty_paths, "empty directory created:", (output_root / "empty").exists())
```

成功下载得到本地 Path，实际文件为 result.bin、4 字节 FAKE；列表没有 attrs。
文件格式应由对应读取器确认，路径/扩展名并不证明内容正确。
底层 FilesInfo 与文件副作用的区别、覆盖与部分完成见
{doc}`文件清单 <low-level/file-list>`、{doc}`文件下载 <low-level/downloads>`；
格式化保存成功空清单的现有 IndexError 见 {doc}`格式化保存 <low-level/save-as-file>`。

```{code-cell} ipython3
:tags: [remove-cell]

check_results(table, cleaned, invalid, field, celsius, empty_table, empty_field,
              paths, empty_paths, output_root, transport)
```

```{code-cell} ipython3
print("API requests:", len(transport.calls) - sum(response.streamed for response in transport.responses),
      "streamed file bodies:", sum(response.streamed for response in transport.responses))
workspace.cleanup()
print("temporary directory removed:", not output_root.exists())
```

## 字符串和 bytes 的后续读取

{doc}`序列化 <low-level/serialization>` 返回 str，需按实际格式解析并检查业务状态；
可解析 JSON 不保证 returnCode 成功。{doc}`数据块 <low-level/data-block>` 返回
DataBlock 的名称和 bytes，应先检查状态、非空及已确认的内容格式，再使用读取器；
名称不作为本地文件路径，UTF-8 或表格转换没有通用保证。数据块真实服务能力仍待确认。

本页未请求真实服务。替换客户端及原生业务参数的方法见
{doc}`配置介绍 <configuration/index>` 与对应业务指南；真实单位、缺测和质量策略
必须由实际资料定义确认，不能复用本例人工值。完整响应字段见
{doc}`响应对象参考 </reference/responses>`；完整入口见
{doc}`高层接口 <high-level/index>`、{doc}`底层 MUSIC 接口 <low-level/index>`。
