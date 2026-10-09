---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 可执行教程页面模板

## 业务目的

本模板以两个虚构站点说明如何查询地面观测表格。复制模板到目标章节后，应将标题、参数、结果和链接改成该场景的实际内容。

本页使用人工合成数据，无需 CMADaaS 账号。数据准备和客户端注入代码默认折叠，可展开查看；实现方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 参数说明

`SYNTHETIC_STATION` 是示例资料代码；时间 `2026-01-02` 是固定的合成时间。`elements` 指定返回的四列，其中 `TEM` 在此示例中只是字符串值，不代表真实地面气温的单位。

```{code-cell} ipython3
:tags: [hide-input]

# 辅助代码来自本仓库，不随 nuwe_cmadaas wheel 分发。
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

```{code-cell} ipython3
:tags: [remove-cell]

assert table["Station_Id_C"].tolist() == ["FAKE001", "FAKE002"]
assert table["TEM"].tolist() == ["280.0", "281.5"]
assert client.calls[0][1] == "getSurfEleByTime"
```

## 常见错误

`FakeClient` 只接受上面登记的精确请求。修改资料代码、时间或参数后，未登记的调用会立即报错。真实服务调用还需要有效配置和对应资料权限。

## 对应底层 interface

本调用使用 `getSurfEleByTime`，返回 `Array2D`，再由高层函数转换为 `pandas.DataFrame`。

## 替换为真实服务

从实际配置创建客户端，并将资料代码、站号及时间换成真实服务支持的值。真实时间应按运行日期计算，不能沿用固定的合成日期。配置入口见 {doc}`配置介绍 </guide/configuration/index>`。

## API reference

参见 {doc}`高层接口参考 </reference/high-level>`。
