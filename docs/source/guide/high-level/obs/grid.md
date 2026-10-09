---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面格点数据

## 业务目的

用 `retrieve_obs_grid()` 读取一个 2×3 的格点场，并查看坐标、变量名和单位。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 参数说明

`SYNTHETIC_GRID` 和 `synthetic_temperature` 只用于离线示例。固定时次是 `2026-01-02`；合成数组的 `K` 单位仅描述本例数值。真实资料的要素、区域和单位应以对应资料目录及返回结果为准。

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

from examples._support import FakeClient, make_grid_array2d_response

client = FakeClient()
client.register(
    "callAPI_to_gridArray2D",
    "getSurfEleGridByTime",
    {
        "dataCode": "SYNTHETIC_GRID",
        "fcstEle": "synthetic_temperature",
        "time": "20260102000000",
    },
    make_grid_array2d_response(),
)
```

## API 调用与返回结果

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_grid

field = retrieve_obs_grid(
    "SYNTHETIC_GRID",
    parameter="synthetic_temperature",
    time=pd.Timestamp("2026-01-02"),
    client=client,
)
field
```

返回值是 `xarray.DataArray`。维度为 `latitude: 2`、`longitude: 3`，坐标分别是 `[30, 31]` 和 `[110, 111, 112]`。下面直接显示六个合成值：

```{code-cell} ipython3
field.values
```

```{code-cell} ipython3
:tags: [remove-cell]

assert field.dims == ("latitude", "longitude")
assert field.shape == (2, 3)
assert field.latitude.values.tolist() == [30.0, 31.0]
assert field.longitude.values.tolist() == [110.0, 111.0, 112.0]
assert field.values.tolist() == [[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]]
assert field.name == "synthetic_temperature"
assert field.attrs["units"] == "K"
assert client.calls[0][1] == "getSurfEleGridByTime"
```

## 常见错误

模拟客户端只接受已登记的参数；改动资料代码、要素或时次会立即报错。真实服务的资料可用性和要素单位须单独核对。

## 对应底层 interface

本例选择 `getSurfEleGridByTime`，底层返回 `GridArray2D`，高层转换为 DataArray。

## 替换为真实服务

换成账号可访问的资料代码、要素与近期时次；需要限定空间范围时使用公开 `region=` 参数。高层 `config=` 使用 CedarKit YAML，或显式传入真实 `client=`。配置见 {doc}`配置介绍 </guide/configuration/index>`，按资料类别选择动态时次见 {doc}`测试与动态时间 </development/testing>`。

## API reference

参见 {doc}`高层接口参考 </reference/high-level>`。
