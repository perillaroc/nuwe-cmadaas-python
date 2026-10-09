---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层序列化：JSON、XML、文本与 HTML 字符串

## 用途与示例来源

用 {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_serializedStr` 请求服务支持的
格式，得到 UTF-8 解码后的原始 str，再按对应格式解析。此方法不写文件，不返回
Array2D/DataFrame，也没有 request、ok、attrs 或 raise_for_error。
需要由服务保存并下载格式化文件时，见 {doc}`格式化文件保存 <save-as-file>`。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 MUSIC 客户端经精确 `SyntheticTransport` 读取人工响应文本，执行生产请求与
UTF-8 解码；未知请求立即失败，没有网络回退，不替换公开方法。
四种格式都描述同一个虚构点 `(30,110)`、固定起报时次 `20260102060000`、
103/2 米层次、24 小时时效和温度字符串 `"280.0"`。温度人工按 K 定义，但正文没有
单位字段，不据此推断真实资料单位。合成格式用于教学，不承诺所有服务输出有相同结构。

## 原生参数与格式优先级

| 参数 | 本例值与行为 |
| --- | --- |
| interface_id | `getNafpEleAtPointByTimeAndLevelAndValidtime` |
| params | 原生 dataCode/fcstEle/time/levelType/fcstLevel/validTime/latLons |
| data_format | `json/xml/text/html`，是否支持由接口/资料/服务决定，客户端不做格式白名单校验 |
| params["dataFormat"] | 缺失时补入 data_format；**已有值优先，不覆盖** |
| server_id | 可选节点，覆盖本次请求；省略使用客户端配置 |

不要传高层 parameter/start_time/forecast_time，签名和认证封装由客户端构造。
本方法会修改调用者的 params，因此每种格式使用新字典，避免沿用之前补入的 dataFormat。

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

from examples.music.serialization import make_serialization_client, check_serialization_results

client, transport = make_serialization_client()
```

(llr-001)=
## JSON：原始字符串再解析

创建一个空临时目录用于核对没有写文件；目录是示例创建的，不是序列化方法创建的。

```{code-cell} ipython3
from tempfile import TemporaryDirectory
from nuwe_cmadaas.music import CMADaaSClient

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
base = {
    "dataCode": "SYNTHETIC_SERIALIZED", "fcstEle": "synthetic_temperature",
    "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "latLons": "30.0/110.0",
}
queries, contents = {}, {}
queries["json"] = base.copy()
contents["json"] = client.callAPI_to_serializedStr(interface_id, queries["json"], "json")
print(type(contents["json"]).__name__, "dataFormat:", queries["json"]["dataFormat"])
print(contents["json"])
```

```{code-cell} ipython3
import json

payload = json.loads(contents["json"])
{"returnCode": payload["returnCode"], "rows": payload["DS"],
 "temperature_type": type(payload["DS"][0]["synthetic_temperature_103"]).__name__}
```

JSON 能解析不等于业务成功，应先检查 returnCode 与结构，再使用 DS。
人工数值仍为字符串，客户端不自动数值化、换算单位或处理缺测。

(llr-002)=
## XML

```{code-cell} ipython3
import xml.etree.ElementTree as ET

queries["xml"] = base.copy()
contents["xml"] = client.callAPI_to_serializedStr(interface_id, queries["xml"], "xml")
print(contents["xml"])
xml_root = ET.fromstring(contents["xml"])
print("returnCode:", xml_root.attrib["returnCode"], "record:", xml_root.find("R").attrib)
```

本例 Response/R 结构由辅助代码构造，字段为 XML 属性字符串；真实结构以服务为准。

(llr-003)=
## text

```{code-cell} ipython3
queries["text"] = base.copy()
contents["text"] = client.callAPI_to_serializedStr(interface_id, queries["text"], "text")
print(contents["text"])
```

本例第一行表示状态，第二行为列名，第三行为点记录。方法保留原文，不解析为表格；
不能假设所有文本格式都用同样分隔符或字段顺序。

(llr-004)=
## HTML

```{code-cell} ipython3
queries["html"] = base.copy()
contents["html"] = client.callAPI_to_serializedStr(interface_id, queries["html"], "html")
print(contents["html"])
```

输出展示 HTML 源码，API 返回仍是 str，不会自动渲染、保存或转为 DataFrame。
此处的 well-formed table 是人工样例，不代表所有服务 HTML 都可以用 XML 解析器处理。

## 已有 dataFormat 保留

即使 data_format 传 xml，params 已有 json 时，请求与结果仍为 JSON：

```{code-cell} ipython3
preserved = {**base, "dataFormat": "json"}
preserved_content = client.callAPI_to_serializedStr(interface_id, preserved, "xml")
{"dataFormat": preserved["dataFormat"], "result_format": "json",
 "same_as_json": preserved_content == contents["json"]}
```

更换格式时新建参数字典，或明确修改/移除 dataFormat。data_format 本身不转换已经
取得的内容；服务支持的格式也不能仅凭扩展名或客户端存在该方法判断。

## 兼容错误文本与原始业务失败

已识别的网关失败返回历史拼写 `getway error:`，并不抛结构化业务异常：

```{code-cell} ipython3
errors = {}
gateway_params = {**base, "dataCode": "SYNTHETIC_GATEWAY"}
errors["gateway"] = client.callAPI_to_serializedStr(interface_id, gateway_params, "json")
print(type(errors["gateway"]).__name__, errors["gateway"])
```

连接处理的请求异常（例如超时）兼容返回 `"Error retrieving data"`。
其他兼容分支可能使用 `parse getway return string error:`。
这些都不是成功正文，不能直接交给 JSON/XML 解析器当作业务数据。
但只检查错误前缀仍不够：没有网关 flag 的格式化业务失败可以按原文返回，
以下字符串能解析为 JSON，returnCode 却非零：

```{code-cell} ipython3
business_params = {**base, "dataCode": "SYNTHETIC_ERROR"}
errors["business"] = client.callAPI_to_serializedStr(interface_id, business_params, "json")
business_error = json.loads(errors["business"])
print("raw:", errors["business"])
print("business status:", business_error["returnCode"], business_error["returnMessage"])
```

方法没有 strict 参数，也不保证所有异常都会转为字符串；无效 UTF-8 等解码错误可直接抛出：

```{code-cell} ipython3
try:
    client.callAPI_to_serializedStr(interface_id, {**base, "dataCode": "SYNTHETIC_UTF8"}, "json")
except UnicodeDecodeError as error:
    errors["utf8"] = type(error).__name__
    print("propagated:", errors["utf8"])
else:
    raise AssertionError("invalid UTF-8 must propagate")
```

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
assert preserved_content == contents["json"]
check_serialization_results(contents, queries, preserved, errors, output_root, transport)
```

```{code-cell} ipython3
print("本地文件：", [path.name for path in output_root.iterdir()])
workspace.cleanup()
print("临时目录已清理：", not output_root.exists())
```

## 已有在线记录与真实替换

LLR-001～004 在 2026-10-08 使用 GFS 预报资料 `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE`、
TEM、103/2 米、24 小时及北京单点分别通过 JSON/XML/text/HTML 原始字符串验证。
本次保留记录，不将人工数据计为新在线通过。服务是否支持格式需逐接口/资料核对。

下面按动态三天前 06 时查询 JSON，并检查兼容错误文本、大小、业务状态及一条记录。
需真实 INI、账号与服务，**不在文档构建时执行**：

```python
import json
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
real_params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"), "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "latLons": "39.9/116.4",
}
real_content = real_client.callAPI_to_serializedStr(
    "getNafpEleAtPointByTimeAndLevelAndValidtime", real_params, "json",
)
if not real_content or len(real_content) > 4096 or real_content.startswith(
    ("getway error:", "parse getway return string error:", "Error retrieving data")
):
    raise RuntimeError("Unexpected serialized response")
real_payload = json.loads(real_content)
if str(real_payload.get("returnCode")) != "0" or len(real_payload.get("DS", [])) != 1:
    raise RuntimeError("Expected one successful point record")
```

字符数检查在响应已读取后进行，不是传输字节上限。真实运行还需核对记录的位置、
起报时间、层次、时效和 TEM_103 的有效数值。其他格式仍需按实际结构处理，
不要将 XML/text/HTML 结果交给 json.loads。
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，日期/案例见
{doc}`测试与动态时间 </development/testing>`，签名和兼容性见
{doc}`客户端参考 </reference/client>`、{doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。

共享脚本同时验证字符串与保存流程，从源码仓库根目录运行：

```bash
uv run python -m examples.music.serialization
```

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。
