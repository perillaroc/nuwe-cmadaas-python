---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 地面站点数据

## 业务目的

用 `retrieve_obs_station()` 获取站点观测表格。本页先用两个虚构站点展示最小调用及 `pandas.DataFrame` 返回值。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 参数说明

`SYNTHETIC_STATION` 是虚构资料代码；`2026-01-02` 是固定合成时间。`elements` 指定四个原始列名，其中 `TEM` 在此示例中只有字符串值，不代表真实地面气温单位。

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

from examples._support import FakeClient, make_array2d_response

client = FakeClient()
client.register(
    "callAPI_to_array2D",
    "getSurfEleByTime",
    {
        "dataCode": "SYNTHETIC_STATION",
        "elements": "Station_Id_C,Lat,Lon,TEM",
        "orderby": "Station_ID_d:asc",
        "times": "20260102000000",
    },
    make_array2d_response(),
)
```

## API 调用与返回结果

```{code-cell} ipython3
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

table = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    client=client,
)
table
```

结果的两行站号是 `FAKE001` 和 `FAKE002`；`Lat`、`Lon`、`TEM` 都保留响应中的字符串形式。计算前应按业务含义显式转换数值列。

```{code-cell} ipython3
:tags: [remove-cell]

assert table.shape == (2, 4)
assert table.columns.tolist() == ["Station_Id_C", "Lat", "Lon", "TEM"]
assert table["Station_Id_C"].tolist() == ["FAKE001", "FAKE002"]
assert table["TEM"].tolist() == ["280.0", "281.5"]
assert client.calls[0][1] == "getSurfEleByTime"
```

## 常见错误

模拟客户端只接受已登记的精确请求；更换参数会立即报错。真实服务还需要有效配置和相应资料权限。

## 对应底层 interface

该请求选择 `getSurfEleByTime`，底层返回 `Array2D`，高层再转换成 DataFrame。

## 替换为真实服务

使用账号可访问的真实资料代码、站号和按运行日期计算的时间。高层 `config=` 是 CedarKit YAML 路径或配置对象；显式提供 `client=` 时使用该客户端。配置说明见 {doc}`配置介绍 </guide/configuration/index>`，日期规则见 {doc}`测试与动态时间 </development/testing>`。

以下调用需要真实服务，不在文档构建时执行：

```python
retrieve_obs_station(
    "SURF_CHN_MUL_HOR",
    station="YOUR_STATION_ID",
    time=pd.Timestamp.now().normalize() - pd.Timedelta(days=1),
    config="/path/to/cedarkit.yaml",
)
```

## API reference

参见 {doc}`高层接口参考 </reference/high-level>`。
