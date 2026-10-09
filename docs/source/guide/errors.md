---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 错误处理：默认返回、strict 与本地异常

## 选择控制流

高层默认 strict=False：失败响应返回 MusicError(code, message)，并发出兼容弃用警告；
strict=True：失败响应转成 CMADaaSError 的具体子类。成功返回类型不受 strict 改变，
合法空结果也不因此抛异常。**strict 不把全部 Python 异常转换成业务错误。**
结果数值化、单位/缺测、attrs 和空结果见 {doc}`使用返回结果 <results>`。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
共享准备在 examples/high_level/handling.py，真实客户端经 SyntheticTransport
解码人工 protobuf；未知请求立即失败，无网络回退，不替换公开方法。
错误码 -11234 和文案为人工构造，不表示某个真实资料的“无数据”约定。

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
from examples.high_level.handling import make_errors_client, check_errors

client, transport = make_errors_client()
```

(legacy-errors)=
## 默认模式：显式识别 MusicError

```{code-cell} ipython3
import pandas as pd
import warnings
from nuwe_cmadaas.music import MusicError
from nuwe_cmadaas.obs import retrieve_obs_station

time = pd.Timestamp("2026-01-02")
common = {"elements": "Station_Id_C,TEM", "time": time, "client": client}
with warnings.catch_warnings(record=True) as warning_records:
    warnings.simplefilter("always", DeprecationWarning)
    legacy = retrieve_obs_station("SYNTHETIC_FAILURE", **common)
notices = [str(item.message) for item in warning_records]
if isinstance(legacy, MusicError):
    print("MusicError:", legacy.code, legacy.message)
else:
    print(legacy)
print("warning:", notices[0])
print("truth value:", bool(legacy), "is exception:", isinstance(legacy, BaseException))
```

MusicError 是普通 dataclass，只有 code/message，不是 Exception，也没有 ok/request。
它的真值为 True，不能用 `if result:` 判成功；必须用 isinstance，之后才操作表格、格点或路径。
DeprecationWarning 通常受 Python 的默认过滤隐藏，此处主动捕获并显示。
不要把任意 MusicError 当成正常空查询，也不要尝试 `raise legacy`。

(strict-errors)=
## strict=True：保留错误类别与上下文

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

caught = {}
try:
    result = retrieve_obs_station("SYNTHETIC_FAILURE", **common, strict=True)
except CMADaaSError as error:
    caught["strict"] = error
    print(type(error).__name__, "code:", error.error_code, "message:", error.server_message)
    print("interface:", error.interface_id, "params:", error.params)
else:
    print("success rows:", len(result))
```

示例使用宽基类展示错误信息；应用可按具体类型选择处理路径。
以下两个请求展示认证失败和坏 protobuf 的不同类别：

```{code-cell} ipython3
for name, code in [("auth", "SYNTHETIC_AUTH"), ("decode", "SYNTHETIC_DECODE")]:
    try:
        retrieve_obs_station(code, **common, strict=True)
    except CMADaaSError as error:
        caught[name] = error
        print(name, type(error).__name__, error.error_code, error.interface_id)
```

| 失败响应错误码 | raise_for_error / 高层 strict 的类别 |
| --- | --- |
| -1004 | CMADaaSAuthenticationError |
| -10001 | CMADaaSTransportError |
| -10003 | CMADaaSDecodeError |
| -10004 | CMADaaSDownloadError |
| 其他非零错误码 | CMADaaSRequestError |

这是当前客户端的分类映射，不是全部服务错误码规范。
名称为 TransportError 也不保证故障在网络：例如保存目标 None 的本地路径问题
兼容返回 -10001，见 {doc}`格式化保存 <low-level/save-as-file>`。
收到业务失败不应无条件重试或改参数绕过，应先核对权限、资料、时次和接口。
本页不增加重试策略；已有连接策略见 {doc}`底层配置 <configuration/music-client>`。

(low-level-errors)=
## 底层：先检查响应，再转换

底层 protobuf 方法没有 strict 参数，失败通常仍返回响应对象。明确传递错误上下文：

```{code-cell} ipython3
interface_id = "getSurfEleByTime"
params = {"dataCode": "SYNTHETIC_FAILURE", "elements": "Station_Id_C,TEM",
          "times": "20260102000000", "orderby": "Station_ID_d:asc"}
raw = client.callAPI_to_array2D(interface_id, params)
print(type(raw).__name__, "ok:", raw.ok, "code:", raw.request.error_code)
try:
    raw.raise_for_error(interface_id=interface_id, params={**params, "token": "EXAMPLE_TOKEN"})
except CMADaaSError as error:
    caught["raw"] = error
    print(type(error).__name__, "context:", error.params)
    print("request_id:", error.request_id, "retries:", error.retries)
```

token 在此仅为人为添加的错误上下文，没有作为请求参数发送。
params 中 password/passwd/pwd/sign/token/authorization 键按大小写不敏感规则递归遮盖。
此保护针对结构化 params，不保证服务 message、自定义字符串或原始请求全文安全；
避免记录带认证的 URL 或完整配置，日志策略见配置指南。
异常的 request_id/retries 在此是 None/0，不能当作连接统计；cause/__cause__ 在适用分支
可以携带底层异常，并非每个错误都有。不要假定所有上下文字段必然可用。

Array2D 和格点提供的转换会检查失败状态，但转换时不会自动保存上次 raise_for_error 的参数：

```{code-cell} ipython3
try:
    raw.to_pandas()
except CMADaaSError as error:
    caught["conversion"] = error
    print(type(error).__name__, "interface:", error.interface_id, "params:", error.params)
```

成功 response.raise_for_error 返回同一对象，可串联使用。DataBlock 的转换未实现，
to_pandas/to_xarray 直接抛 NotImplementedError，应显式检查状态再按格式读取 bytes。
serializedStr 没有响应对象，可能返回历史 `getway error:`、`Error retrieving data`
等错误文本，也可能原样返回业务失败 JSON；其他解码异常可直接抛出，见
{doc}`序列化 <low-level/serialization>`。不能用一条统一的 ok/strict 规则处理这两种返回。

(local-errors)=
## 本地参数和配置错误不受 strict 隐藏

非法参数与不支持的组合在请求前拒绝；即使 strict=False，也直接抛出：

```{code-cell} ipython3
local_errors = {}
for name, selectors in [
    ("count", {"time": time, "elements": "Station_Id_C,TEM", "count": 0}),
    ("time", {"time": "2026-01-02", "elements": "Station_Id_C,TEM"}),
    ("latest_filter", {"time": pd.Timedelta(hours=6), "station": "FAKE001"}),
]:
    before = len(transport.calls)
    try:
        retrieve_obs_station("SYNTHETIC_FAILURE", client=client, strict=False, **selectors)
    except (ValueError, TypeError, CMADaaSError) as error:
        local_errors[name] = type(error).__name__
        print(name, local_errors[name], "API requests:", len(transport.calls) - before)
```

本例为 count=0→ValueError、字符串 time→TypeError、latest 加站号筛选→UnsupportedQueryError。
UnsupportedQueryError 继承 CMADaaSQueryError/CMADaaSError，但其他参数错误仍可能是
普通 TypeError/ValueError。不同入口允许的组合以各业务指南为准。

以下仅尝试读取本例空临时目录中的不存在配置文件，不读用户默认配置或实际凭据：

```{code-cell} ipython3
from tempfile import TemporaryDirectory

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
for name, strict in [("config_default", False), ("config_strict", True)]:
    try:
        retrieve_obs_station(
            "SYNTHETIC_FAILURE", elements="Station_Id_C,TEM", time=time,
            config=output_root / "missing.yaml", strict=strict,
        )
    except FileNotFoundError as error:
        local_errors[name] = type(error).__name__
        print(name, local_errors[name])
```

YAML 加载仍可能直接抛 FileNotFoundError、KeyError 或 YAML 解析异常，未统一转为
CMADaaSConfigurationError；显式 client 注入会跳过高层配置加载。
本地数值化、Unicode 解码、未实现转换以及文件操作也可能直接抛 Python 异常。
不要用一个捕获 CMADaaSError 的分支声称覆盖所有错误，或把程序错误当成正常无数据。

(empty-vs-error)=
## 空成功与失败分别处理

```{code-cell} ipython3
empty = retrieve_obs_station("SYNTHETIC_EMPTY", **common, strict=True)
print(type(empty).__name__, "shape:", empty.shape, "columns:", empty.columns.tolist(), "empty:", empty.empty)
```

本例成功空表为 (0,2)，仍含 Station_Id_C/TEM 列；没有 MusicError，也不抛 strict 异常。
若业务预期非空，需要调用者另外检查 empty/size/列表长度；“没有数据”是否用空结果或
非零错误码由具体服务契约决定，不能把业务失败通用地改成空表/空格点/[]。
成功空下载返回 []；批量下载后项失败可能保留前项文件，没有整批回滚，见
{doc}`文件下载 <low-level/downloads>`。格式化保存成功空清单仍有 IndexError，
不套用 downFile 的空语义；数据块 ok=True 但 bytes 为空不能证明在线支持。

```{code-cell} ipython3
:tags: [remove-cell]

check_errors(legacy, notices, caught, raw, empty, local_errors, output_root, transport)
```

```{code-cell} ipython3
print("API requests:", len(transport.calls), "all responses closed:",
      all(response.closed for response in transport.responses))
print("files written:", [path.name for path in output_root.iterdir()])
workspace.cleanup()
print("temporary directory removed:", not output_root.exists())
```

本页未访问真实服务；模拟错误不作为在线能力或真实错误码验收结果。
替换真实客户端的方法见 {doc}`配置介绍 <configuration/index>`；
完整方法签名和兼容规则见 {doc}`高层参考 </reference/high-level>`、
{doc}`客户端参考 </reference/client>`、{doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。
