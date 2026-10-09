---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 无账号快速入门

用高层函数 `retrieve_obs_station()` 完成一次地面站点查询，得到 `pandas.DataFrame`。先按 {doc}`安装 <installation>` 取得源码并安装主库；在仓库根目录，将展开的准备代码和 API 调用代码依次复制到 `quickstart.py`，使用同一 Python 环境运行 `python quickstart.py`。页面中的代码也会在文档构建时自动执行。

本页使用人工合成数据，无需 CMADaaS 账号、配置文件或外部网络。数据准备与客户端注入默认折叠，可展开查看；数据来源和执行路径见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 准备一个模拟客户端

`SYNTHETIC_STATION` 是虚构资料代码，`2026-01-02` 是固定合成时间。`elements` 指定返回的四个原始列名。模拟客户端登记该请求并提供真实 `Array2D` 响应对象，高层函数负责组装参数和转换表格。

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

## 调用高层 API 并查看结果

显式传入 `client=client` 后，函数使用该模拟客户端。`strict=True` 会在服务响应报错时抛出异常；本例返回成功响应。

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
print(table.to_string(index=False))
```

输出包含 `FAKE001`、`FAKE002` 两个虚构站点。`Lat`、`Lon`、`TEM` 保留响应中的字符串，`TEM` 的 `280.0` 和 `281.5` 是人工数值，不代表真实地面气温或单位。业务计算前应按资料定义显式转换数值列。

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(table, pd.DataFrame)
assert table.columns.tolist() == ["Station_Id_C", "Lat", "Lon", "TEM"]
assert table.values.tolist() == [
    ["FAKE001", "30.0", "110.0", "280.0"],
    ["FAKE002", "31.0", "111.0", "281.5"],
]
assert len(client.calls) == 1
assert client.calls[0][0:2] == ("callAPI_to_array2D", "getSurfEleByTime")
```

这个调用对应底层 `getSurfEleByTime` 接口：高层取得 `Array2D` 后调用 `to_pandas()`，所以业务代码可直接使用 DataFrame。完整参数见 {doc}`高层接口参考 </reference/high-level>`。

## 常见问题与真实服务

若无法导入 `nuwe_cmadaas`，确认当前 Python 来自安装时的虚拟环境；若无法找到 `examples._support`，确认已经取得完整源码，并从仓库根目录运行。更改合成资料代码、时间或要素时，须同步修改模拟客户端登记的请求，否则会抛出 `AssertionError`。

真实服务调用需要可访问的 MUSIC 服务、有效账号和相应资料权限。切换时使用真实资料代码、站号和运行时日期，并用 `config=` 指定 CedarKit YAML 配置，移除模拟 `client=`；同时传入二者时 `client=` 优先。下面的代码需要真实服务，文档构建不会执行：

```python
station_time = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
table = retrieve_obs_station(
    "SURF_CHN_MUL_HOR",              # 改为账号可访问的资料代码
    elements="Station_Id_C,Lat,Lon,TEM",
    station="YOUR_STATION_ID",       # 改为真实站号
    time=station_time,
    config="/path/to/cedarkit.yaml",  # CedarKit YAML
    strict=True,
)
```

高层的 `config=` 与底层 `CMADaaSClient(config_file=...)` 的 MUSIC INI 配置不同，参见 {doc}`配置介绍 </guide/configuration/index>`。真实地面站点案例使用前一天日期；其他资料的在线测试日期约定见 {doc}`测试与动态时间 </development/testing>`。默认 `strict=False` 时，服务错误会返回 `MusicError`，应先判断结果再进行表格操作；`strict=True` 适合本例这样的成功调用路径。

## 下一步

- 阅读 {doc}`接口选择 </guide/choosing-api>`，了解高层业务 API 与底层 MUSIC 客户端的使用方式。
- 继续 {doc}`地面站点 </guide/high-level/obs/station>`、{doc}`地面格点 </guide/high-level/obs/grid>` 或 {doc}`文件下载 </guide/high-level/obs/files>` 的合成数据教程。
- 查阅 {doc}`模拟数据与客户端注入 </guide/simulated-data>`，了解响应工厂、请求登记及真实解码路径。
