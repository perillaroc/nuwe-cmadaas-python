# 模拟数据与客户端注入

指南中的离线示例使用人工构造的 MUSIC 响应，无需 CMADaaS 账号。它们展示 `nuwe_cmadaas` 的参数、解码、转换和下载行为；页面显示的站号、日期和数值都不是服务数据。业务教程将数据准备折叠，本章直接展示辅助代码的关键实现，便于检查模拟边界。

## 取得源码并运行示例

辅助模块在源码仓库的 `examples/_support/`，不在 `src/` 内，也不随 `nuwe_cmadaas` wheel 分发。只安装 wheel 无法导入它。取得[源码仓库](https://github.com/perillaroc/nuwe-cmadaas-python)后，从仓库根目录安装文档依赖并运行构建：

```bash
uv sync --group docs
uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html
```

直接运行示例脚本时，以仓库根目录为工作目录，即可使用 `from examples._support import FakeClient`。MyST-NB 页面可能从文档所在目录启动内核，因此模板会从当前目录逐级向上寻找含 `examples/_support/synthetic.py` 的仓库根目录，再将其加入 `sys.path`。复制文档到独立目录执行时，可设置 `NUWE_CMADAAS_REPO_ROOT` 为源码仓库的绝对路径。具体加载代码见仓库的 `docs/templates/executable-page.md`；每个业务页面自行准备客户端，不依赖其他页面执行后的内核状态。

## 合成内容及返回路径

数据由 `examples/_support/synthetic.py` 在本地构造 protobuf 消息，不使用录制的服务响应。固定内容如下：

| 内容 | 合成值 | 含义 |
| --- | --- | --- |
| 时间 | `2026-01-02 00:00:00` | 只用于可重复的示例请求与响应元数据 |
| 站点 | `FAKE001`、`FAKE002` | 虚构站号；`Lat`/`Lon` 是字符串 |
| 站点 `TEM` | `"280.0"`、`"281.5"` | 人工字符串，不作为真实地面气温或单位说明 |
| 格点 | 纬度 `[30, 31]`、经度 `[110, 111, 112]`；数值 `[[280.0, 280.5, 281.0], [281.5, 282.0, 282.5]]` | 2×3 网格，名称 `synthetic_temperature`，合成单位 `K`；矢量格点的 U/V 另用 `[1, …, 6]` 和 `[-1, …, -6]` |
| 文件 | `synthetic.bin`，内容 `b"FAKE"` | 4 字节；清单 URL 为 `https://synthetic.invalid/data.bin` |

表格工厂先填充 `RetArray2D` 的列名、字符串数据和请求信息，再序列化为 bytes；`make_array2d_response()` 调用真实的 `Array2D.create_from_protobuf()`。格点和文件工厂分别生成 `RetGridArray2D`、`RetFilesInfo`，再构造真实的 `GridArray2D`、`FilesInfo` 响应对象。以下是仓库中实际使用的表格消息构造函数：

```{literalinclude} ../../../examples/_support/synthetic.py
:language: python
:pyobject: make_array2d_content
```

高层 `retrieve_obs_station()` 对 `Array2D` 调用 `to_pandas()`，保留原始字符串列；`retrieve_obs_grid()` 对 `GridArray2D` 调用 `to_xarray()`，得到 `latitude/longitude` 维度及 `units` 属性。文件清单仅描述文件，不会写磁盘；高层下载必须经过真实客户端的下载路径，才返回实际存在的 `list[Path]`。这些类型及转换由库本身实现，辅助模块没有手写 DataFrame 或替换公开检索函数。

格点和文件清单的响应工厂也直接调用相应响应类的 protobuf 解码方法：

```{literalinclude} ../../../examples/_support/synthetic.py
:language: python
:pyobject: make_grid_array2d_response
```

```{literalinclude} ../../../examples/_support/synthetic.py
:language: python
:pyobject: make_files_info_response
```

## 高层：注入 FakeClient

`FakeClient` 按方法名、interface ID 和完整 MUSIC 参数登记真实响应对象。公开高层函数仍负责选择 interface、组装参数、处理错误和转换结果。`FakeClient` 记录每次调用；没有匹配登记的请求抛出 `AssertionError`，不会访问网络。以下展示参数键函数及完整类实现，包含登记、调用记录和返回路径：

```{literalinclude} ../../../examples/_support/clients.py
:language: python
:pyobject: _parameter_key
```

```{literalinclude} ../../../examples/_support/clients.py
:language: python
:pyobject: FakeClient
```

从仓库根目录运行以下代码，可查看匹配请求的调用记录与转换结果：

```python
import pandas as pd
from examples._support import FakeClient, make_array2d_response
from nuwe_cmadaas.obs import retrieve_obs_station

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
table = retrieve_obs_station(
    "SYNTHETIC_STATION",
    elements="Station_Id_C,Lat,Lon,TEM",
    time=pd.Timestamp("2026-01-02"),
    client=client,
)
print(table[["Station_Id_C", "TEM"]].to_string(index=False))
print(client.calls[0][0:2])
```

`table` 的两行站号是 `FAKE001`、`FAKE002`；`TEM` 仍是 `"280.0"`、`"281.5"`。调用记录中的方法与接口分别是 `callAPI_to_array2D`、`getSurfEleByTime`。`client=client` 是公开调用的显式依赖；高层传入该参数时忽略 `config=`。`FakeClient` 可演示高层格点转换，但其文件方法只返回 `FilesInfo`，不能代替磁盘下载。

## 底层：注入 transport 并写入文件

底层示例使用真实 `CMADaaSClient`。`make_synthetic_music_client()` 填写虚构服务地址和凭据，并通过 `transport=` 注入 `SyntheticTransport`；也可在自行构造客户端时通过 `session=` 注入。合成 transport 只接受明确登记的 MUSIC 请求及 `.invalid` 下载 URL。未知方法、interface、参数或 URL 都会立即失败，没有网络回退。实际客户端构造如下：

```{literalinclude} ../../../examples/_support/transport.py
:language: python
:pyobject: make_synthetic_music_client
```

`SyntheticTransport.get()` 严格核对请求并返回 `SyntheticResponse`。protobuf 响应通过 `content` 供真实解码器读取；下载响应只允许 `iter_content()` 流式读取，随后由库内 `Connection.download_file()` 写入临时文件并替换目标文件。登记与读取的关键边界直接见源码：

```{literalinclude} ../../../examples/_support/transport.py
:language: python
:pyobject: SyntheticTransport.register_api
```

```{literalinclude} ../../../examples/_support/transport.py
:language: python
:pyobject: SyntheticTransport.register_download
```

```{literalinclude} ../../../examples/_support/transport.py
:language: python
:pyobject: SyntheticTransport.get
```

```{literalinclude} ../../../examples/_support/transport.py
:language: python
:pyobject: SyntheticResponse.iter_content
```

以下代码从仓库根目录运行，先解码人工表格，再下载 4 字节文件。下载输出只显示文件名和大小，不依赖临时目录的随机路径：

```python
from tempfile import TemporaryDirectory
from pathlib import Path

from examples._support import (
    SyntheticTransport,
    make_array2d_content,
    make_file_bytes,
    make_files_info_content,
    make_synthetic_music_client,
)

params = {"dataCode": "SYNTHETIC"}
transport = SyntheticTransport()
transport.register_api("callAPI_to_array2D", "table", params, make_array2d_content())
transport.register_api("callAPI_to_fileList", "files", params, make_files_info_content())
transport.register_download("https://synthetic.invalid/data.bin", make_file_bytes())
client = make_synthetic_music_client(transport)

table_response = client.callAPI_to_array2D("table", params)
print(table_response.to_pandas()["Station_Id_C"].tolist())
with TemporaryDirectory() as directory:
    files = client.callAPI_to_downFile("files", params, directory)
    path = Path(directory) / files.files_info[0].file_name
    print(path.name, path.stat().st_size, path.read_bytes())
```

`callAPI_to_downFile()` 的签名请求沿用 `callAPI_to_fileList` 方法名，因此上述登记与真实客户端当前行为一致。未登记请求可用 `client.callAPI_to_array2D("unknown", params)` 验证，它会抛出 `AssertionError`。这些地址属于保留的 `.invalid` 域名；transport 拦截所有示例请求，不会对其发出实际 HTTP 请求。

## 业务页如何显示代码

普通业务教程先在可见正文中说明合成数据，并在第一个示例之前链接本章。随后将辅助模块加载、响应准备及 `FakeClient` 或 transport 的创建与注入放在独立 MyST-NB 单元，标记 `:tags: [hide-input]`；读者可展开查看。公开函数的导入、参数、`client=client` 调用和结果放在无隐藏标签的单元。底层 `callAPI_to_*` 调用也直接展示。只为构建校验的断言可另放 `:tags: [remove-cell]` 单元；教学用的异常处理及输出应可见。

`hide-input`、`remove-cell` 仅改变页面呈现，单元仍按顺序执行；不能用 `remove-input` 或 `remove-cell` 藏起准备与注入。完整可执行的 MyST-NB 页面结构见 `docs/templates/executable-page.md`。复制模板后，按 `docs/README.md` 在 `docs/simulated-pages.json` 登记，并运行 `python3 docs/check_simulated_pages.py`。每页必须独立创建客户端，不能依赖别的页面留下的内核变量。

## 切换到真实服务

真实调用要同时替换模拟客户端、虚构资料代码与站号、固定时间。高层可使用 CedarKit YAML 路径或配置对象传给 `config=`；底层 MUSIC INI 文件使用 `CMADaaSClient(config_file=...)`。高层若显式传 `client=`，则使用该客户端并忽略 `config=`。配置入口见 {doc}`配置介绍 </guide/configuration/index>`，在线测试的资料与动态日期约定见 {doc}`测试与动态时间 </development/testing>`。

下面只是**需要真实服务**的调用形式，不会在文档构建时执行。资料代码、站号、时次及配置路径须按账号权限和资料目录选择；不能把合成时间原样带到在线请求：

```python
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

station_time = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
table = retrieve_obs_station(
    "SURF_CHN_MUL_HOR",           # 改为账号可访问的真实资料代码
    elements="Station_Id_C,Lat,Lon,TEM",
    station="YOUR_STATION_ID",    # 改为真实站号
    time=station_time,
    config="/path/to/cedarkit.yaml",  # CedarKit YAML，不是 MUSIC INI
    strict=True,
)
```

三个最小业务示例分别见 {doc}`地面站点指南 </guide/high-level/obs/station>`、{doc}`地面格点指南 </guide/high-level/obs/grid>` 和 {doc}`地面文件下载指南 </guide/high-level/obs/files>`。每页独立准备客户端，并在构建时执行。
