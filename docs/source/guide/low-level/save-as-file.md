---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
simulated_data: true
---

# 底层格式化保存：请求、下载与实际文件

## 用途与示例来源

用 {py:meth}`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_saveAsFile` 请求服务生成
格式化结果，再下载返回清单的**第一项**到指定 file_name。返回 `FilesInfo`，
不是字符串或本地 Path；调用后应检查 request/ok，核对目标文件并解析正文。
只需字符串时见 {doc}`底层序列化 <serialization>`，一般文件批量下载见
{doc}`文件下载 <downloads>`。

本页使用人工合成数据，无需账号。准备默认折叠，可展开查看；实现见
{doc}`模拟数据与客户端注入 </guide/simulated-data>`。
真实 MUSIC 客户端读取人工 RetFilesInfo 并流式下载登记正文，执行生产解码、写文件
和替换；未知请求立即失败，没有网络回退，不替换公开方法。
四种格式描述与序列化页相同的虚构点、固定起报、层次、时效与温度字符串。
准备只创建临时目录并登记响应，不预写结果；实际文件由下面公开调用产生。

## 参数修改与保存目标

| 参数 | 实际行为 |
| --- | --- |
| interface_id / params | 原生点预报接口与 dataCode/fcstEle/time/levelType/fcstLevel/validTime/latLons |
| data_format | 本例 json/xml/text/html；是否支持由服务决定，不做本地格式转换/白名单校验 |
| params["dataFormat"] | 缺失时添加，已有值不被 data_format 覆盖 |
| file_name | 完整本地目标文件名字符串，含目录；直接作为下载目标，不使用返回 FileInfo.file_name 命名 |
| params["savepath"] | 每次替换为 file_name，旧值被覆盖；修改在失败后也保留 |
| server_id | 可选节点，覆盖本次保存请求；省略使用客户端配置 |

方法没有 overwrite 或 strict 参数，已有目标默认替换；有覆盖保护需求时自行选择
新的目标名。服务保存请求禁用读取重试，随后的文件下载仍使用连接的下载重试规则。
方法只下载第一项，不是 downFile 的全清单下载，不能假设多项都会生成本地文件。

```{code-cell} ipython3
:tags: [hide-input]

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

start = Path(os.environ.get("NUWE_CMADAAS_REPO_ROOT", Path.cwd())).resolve()
repo_root = next(
    (path for path in (start, *start.parents)
     if (path / "examples" / "_support" / "synthetic.py").is_file()),
    None,
)
if repo_root is None:
    raise RuntimeError("Run this example from a nuwe-cmadaas-python checkout")
sys.path.insert(0, str(repo_root))

from examples.music.serialization import make_save_client, check_save_results, check_formatted_content

workspace = TemporaryDirectory()
output_root = Path(workspace.name)
client, transport = make_save_client(output_root)
```

(lls-001)=
## JSON 文件

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSClient

interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
base = {
    "dataCode": "SYNTHETIC_SAVE", "fcstEle": "synthetic_temperature",
    "time": "20260102060000", "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "latLons": "30.0/110.0",
}
queries, results = {}, {}
queries["json"] = base.copy()
json_path = output_root / "point.json"
results["json"] = client.callAPI_to_saveAsFile(interface_id, queries["json"], "json", str(json_path))
results["json"].raise_for_error(interface_id=interface_id, params=queries["json"])
{
    "response_type": type(results["json"]).__name__, "ok": results["json"].ok,
    "dataFormat": queries["json"]["dataFormat"],
    "savepath_matches_target": queries["json"]["savepath"] == str(json_path),
    "local_name": json_path.name, "actual_bytes": json_path.stat().st_size,
    "returned_name": results["json"].files_info[0].file_name,
    "returned_save_path": results["json"].files_info[0].save_path,
}
```

目标是 point.json，服务元数据名称是 service-result.json、路径为
`/synthetic/service/result.json`；客户端按指定 file_name 写入，不改写返回的元数据。
不展示随机临时绝对路径，实际大小来自磁盘：

```{code-cell} ipython3
import json

json.loads(json_path.read_text(encoding="utf-8"))
```

格式、扩展名或 ok 都不能代替内容核对。本例 JSON 状态为零，含一条虚构点记录，
温度保持字符串；真实数据仍需验证业务状态、字段和值。

(lls-002)=
## XML 文件

```{code-cell} ipython3
import xml.etree.ElementTree as ET

queries["xml"] = base.copy()
xml_path = output_root / "point.xml"
results["xml"] = client.callAPI_to_saveAsFile(interface_id, queries["xml"], "xml", str(xml_path))
results["xml"].raise_for_error(interface_id=interface_id, params=queries["xml"])
xml_root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
print(xml_path.name, xml_path.stat().st_size, "bytes")
print(xml_root.attrib, xml_root.find("R").attrib)
```

(lls-003)=
## text 文件

```{code-cell} ipython3
queries["text"] = base.copy()
text_path = output_root / "point.text"
results["text"] = client.callAPI_to_saveAsFile(interface_id, queries["text"], "text", str(text_path))
results["text"].raise_for_error(interface_id=interface_id, params=queries["text"])
print(text_path.name, text_path.stat().st_size, "bytes")
print(text_path.read_text(encoding="utf-8"))
```

(lls-004)=
## HTML 文件

```{code-cell} ipython3
queries["html"] = base.copy()
html_path = output_root / "point.html"
results["html"] = client.callAPI_to_saveAsFile(interface_id, queries["html"], "html", str(html_path))
results["html"].raise_for_error(interface_id=interface_id, params=queries["html"])
print(html_path.name, html_path.stat().st_size, "bytes")
print(html_path.read_text(encoding="utf-8"))
```

四文件大小由实际下载生成，当前分别为 161/149/111/255 字节。
这些仅是合成内容规模，不是服务格式的固定长度。HTML 显示源码，不自动渲染。

## dataFormat 保留、savepath 改写及已有目标替换

先把 JSON 本地内容改成 LOCAL，再传已有 dataFormat=json 和旧 savepath。
即使 data_format 传 xml，已有 json 仍优先；savepath 则被新目标覆盖，JSON 重新下载：

```{code-cell} ipython3
json_path.write_bytes(b"LOCAL")
preserved = {**base, "dataFormat": "json", "savepath": "old-path"}
repeated = client.callAPI_to_saveAsFile(interface_id, preserved, "xml", str(json_path))
repeated.raise_for_error(interface_id=interface_id, params=preserved)
{
    "dataFormat": preserved["dataFormat"], "savepath_changed": preserved["savepath"] == str(json_path),
    "actual_bytes": json_path.stat().st_size,
    "parsed_returnCode": json.loads(json_path.read_text(encoding="utf-8"))["returnCode"],
}
```

每次格式调用应新建字典，或明确管理两个原生字段。
`file_name` 的后缀不会自动选择 dataFormat，也不将已有内容转换为另一个格式。

## 服务、网关、解码失败与本地边界

与序列化方法的错误字符串不同，保存通常通过 FilesInfo.request 表达处理过的失败：

```{code-cell} ipython3
from nuwe_cmadaas.music import CMADaaSError

failures = {}
for name, code, filename in [
    ("service", "SYNTHETIC_ERROR", "failed.json"),
    ("gateway", "SYNTHETIC_GATEWAY", "gateway.json"),
    ("decode", "SYNTHETIC_DECODE", "decode.json"),
]:
    query = {**base, "dataCode": code}
    target = output_root / filename
    failures[name] = client.callAPI_to_saveAsFile(interface_id, query, "json", str(target))
    try:
        failures[name].raise_for_error(interface_id=interface_id, params=query)
    except CMADaaSError as error:
        print(name, "ok:", failures[name].ok, type(error).__name__, error.error_code,
              "file_exists:", target.exists(), "params_changed:",
              query["dataFormat"] == "json" and query["savepath"] == str(target))
    else:
        raise AssertionError("failed save must raise")
```

以上三种失败都没有正文下载或本地文件，params 的修改仍保留。
传 file_name=None 会在请求前返回 -10001：dataFormat 已补入，savepath 尚未改写。
这个本地目标错误沿用现有错误码，不能仅凭异常类别推断真的发生了网络故障：

```{code-cell} ipython3
none_params = base.copy()
calls_before = len(transport.calls)
failures["none"] = client.callAPI_to_saveAsFile(interface_id, none_params, "json", None)
{
    "ok": failures["none"].ok, "error_code": failures["none"].request.error_code,
    "dataFormat": none_params["dataFormat"], "savepath_present": "savepath" in none_params,
    "new_requests": len(transport.calls) - calls_before,
}
```

也不是所有失败都返回 FilesInfo。当前实现直接取成功清单第一项，
成功空清单会抛 IndexError，不能把它当作成功空文件或套用 downFile 的空清单语义：

```{code-cell} ipython3
empty_params = {**base, "dataCode": "SYNTHETIC_EMPTY"}
try:
    client.callAPI_to_saveAsFile(interface_id, empty_params, "json", str(output_root / "empty.json"))
except IndexError as error:
    failures["empty"] = type(error).__name__
    print("current empty-list behavior:", failures["empty"],
          "file_exists:", (output_root / "empty.json").exists())
else:
    raise AssertionError("current empty save-list behavior must remain explicit")
```

本文记录现有兼容行为，不更改生产保存策略；其他本地配置/参数异常仍可直接抛出。
单文件下载使用临时文件并替换目标，失败清理临时文件；HTTP Content-Length 检查
不等于 FileInfo.size 或格式内容校验。此方法没有本地输出字节上限，大小检查需调用方安排。

```{code-cell} ipython3
:tags: [remove-cell]

assert isinstance(client, CMADaaSClient)
assert len(transport.calls) == calls_before + 1
assert none_params == {**base, "dataFormat": "json"}
check_save_results(results, queries, preserved, failures, output_root, transport)
```

```{code-cell} ipython3
print("已保存文件：", [(path.name, path.stat().st_size) for path in sorted(output_root.iterdir())])
workspace.cleanup()
print("临时文件已清理：", not output_root.exists())
```

## 已有在线记录与真实替换

LLS-001～004 于 2026-10-08 使用 GFS/TEM/103/2 米/24 小时及北京单点分别通过
JSON/XML/text/HTML 保存和内容验证。本次保留这些记录，不将合成文件计为新在线通过。
仅使用服务确实支持的格式和资料；同名接口不代表任意 dataFormat 都可用。

下面使用动态三天前 06 时保存 JSON，核对实际大小和业务状态。需真实配置、账号与
服务，**不在文档构建时执行**；已有目标会替换：

```python
from pathlib import Path
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
real_interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtime"
real_params = {
    "dataCode": "NAFP_FOR_FTM_GRAPES_CFSV2_NEHE", "fcstEle": "TEM",
    "time": recent_cycle.strftime("%Y%m%d%H%M%S"), "levelType": "103", "fcstLevel": "2",
    "validTime": "24", "latLons": "39.9/116.4",
}
real_target = Path("./cmadaas-formatted/point.json")
real_result = real_client.callAPI_to_saveAsFile(real_interface_id, real_params, "json", str(real_target))
real_result.raise_for_error(interface_id=real_interface_id, params=real_params)
if not real_target.is_file() or not 0 < real_target.stat().st_size <= 1024 * 1024:
    raise RuntimeError("Unexpected saved-file size")
real_payload = json.loads(real_target.read_text(encoding="utf-8"))
if str(real_payload.get("returnCode")) != "0" or len(real_payload.get("DS", [])) != 1:
    raise RuntimeError("Expected one successful point record")
```

1 MiB 检查发生于已下载之后，不是传输上限；应选少点、小结果并核对实际资料字段和值。
配置见 {doc}`底层客户端配置 </guide/configuration/music-client>`，日期/案例见
{doc}`测试与动态时间 </development/testing>`，完整签名见
{doc}`客户端参考 </reference/client>`。

共享脚本从源码仓库根目录运行，验证四种格式、参数修改、兼容失败、实际文件与清理：

```bash
uv run python -m examples.music.serialization
```

## 通用结果与错误指南

字符串数值化、单位/缺测、attrs 与空结果见 {doc}`使用返回结果 </guide/results>`；
默认 MusicError、strict、底层响应状态与本地异常见 {doc}`错误处理 </guide/errors>`。
