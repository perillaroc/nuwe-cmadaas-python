# 底层配置：MUSIC INI 与构造参数

`CMADaaSClient` 用于直接调用 MUSIC interface，也可通过高层函数的 `client=` 复用。本页说明 INI、配置字典和显式参数的关系。所有账号、服务地址和路径均为占位值；代码块供手动运行，文档构建不向真实服务发请求。

高层 YAML 的文件查找见 {doc}`高层配置 <high-level>`。若只需无账号运行教程，参见 {doc}`快速入门 </getting-started/quickstart>` 与 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## 显式读取 MUSIC INI

MUSIC 配置文件通常命名为 `client.config`，内容为 INI。节名必须是 `[Pb]`，连接字段如下：

```ini
[Pb]
music_server = YOUR_MUSIC_HOST
music_port = 80
music_ServiceId = 0
music_connTimeout = 10
music_readTimeout = 60
```

INI 只读取上述连接字段，不读取账号和密码。端口、连接超时和读取超时按整数解析，节点 ID 按字符串读取。凭据通过构造参数或配置字典提供：

```python
from pathlib import Path
from nuwe_cmadaas.music import CMADaaSClient

client = CMADaaSClient(
    config_file=Path("/path/to/client.config"),
    user="YOUR_USER",
    password="YOUR_PASSWORD",
)
```

只有传入 `config_file=` 才会读取 INI。`CMADaaSClient()` 不自动加载当前目录的 `client.config`，也不读取 `CEDARKIT_CONFIG` 或默认的 CedarKit YAML。文件名可以自定；相对路径按进程当前工作目录解析，字符串中的 `~` 不自动展开。

## 直接传入连接参数

不使用文件时，通过构造参数提供连接与认证信息：

```python
client = CMADaaSClient(
    server_ip="YOUR_MUSIC_HOST",
    server_port=80,
    server_id="0",
    connection_timeout=10,
    read_timeout=60,
    user="YOUR_USER",
    password="YOUR_PASSWORD",
    log_policy="redacted",
    max_retries=2,
    retry_backoff=0.1,
)
```

| 构造参数 | 对应 YAML / INI 字段 | 用途 |
| --- | --- | --- |
| `server_ip` | `music_server` | 主机或 IP，不含协议和 API 路径 |
| `server_port` | `music_port` | 端口 |
| `server_id` | `music_ServiceId` | 默认服务节点 |
| `connection_timeout` | `music_connTimeout` | 连接超时，秒；客户端属性名为 `connect_timeout` |
| `read_timeout` | `music_readTimeout` | 读取超时，秒 |
| `user` / `password` | YAML 的 `auth`；INI 不读取 | 认证信息 |

显式超时参数可使用浮点数，INI 超时字段需整数。客户端不会为这些连接与认证字段补默认业务值；全部未提供时会保留 `None`。创建对象不会自动登录或检测服务可达性，应在请求前提供完整配置。

## 字典配置与真实优先级

底层 `config=` 只接受含 `auth`、`server` 的配置字典，不能直接传 YAML 路径。需要 YAML 时先加载：

```python
from nuwe_cmadaas.config import load_cmadaas_config

cmadaas_config = load_cmadaas_config("/path/to/cedarkit.yaml")
client = CMADaaSClient(config=cmadaas_config, connection_timeout=5)
```

各连接字段只在当前值为 `None` 时从后续来源补齐，顺序为：

1. 显式构造参数。
2. `config_file` 指定的 INI。
3. `config` 字典。

认证字段的顺序为“显式 `user` / `password` → `config["auth"]`”，因为 INI 不读取认证。数值 `0` 或空字符串均不等于 `None`，不会被后续来源覆盖。

例如同时传入两种配置：

```python
client = CMADaaSClient(
    config_file="/path/to/client.config",
    config=cmadaas_config,
    server_port=8080,
    connection_timeout=5,
)
```

端口和连接超时使用显式值；主机、节点 ID、读取超时从 INI 取得；账号密码从字典取得。INI 在字典之前读取，缺失或无效的 INI 不会退回字典。请提供完整的 INI 连接字段，或用显式参数补齐其余字段，不能依靠字典填补缺失的 INI 项。通常选择一个配置来源即可；这里给出组合规则是为了说明已有客户端的实际行为。

## 连接、transport 与其他选项

构造函数内部调用 `create_connect(user, password)`，保存认证信息并创建 `Connection`。它是本地初始化，不是服务端登录。后续显式调用此方法会替换客户端账号密码、重建连接对象，但不会重新读取 INI 或 YAML。

默认 transport 为 `requests`。需要连接池时，可传入 `requests.Session()`：

```python
import requests

with requests.Session() as session:
    client = CMADaaSClient(config=cmadaas_config, session=session)
    # 在此上下文内调用 client.callAPI_to_*，或通过高层 client=client 使用。
```

也可注入提供 `get()` 的 `transport=`；`session` 和 `transport` 互斥，同时传入会抛出 `ValueError`。文档的合成 transport 注入方式见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

`max_retries` 默认 `2`（初次请求之外最多两次重试），必须是非负整数；`retry_backoff` 默认 `0.1` 秒，必须非负。幂等读取在超时、连接异常或 HTTP 502/503/504 时按指数间隔重试；这些选项不能通过 INI 或 YAML 设置。

`log_policy` 可选 `full`（默认，记录完整请求 URL）、`redacted`（记录脱敏 URL）和 `summary`（记录请求摘要）。高层函数若需这些选项，应先构造客户端再传入 `client=`。

## 请求节点与常见配置错误

底层 `callAPI_to_*` 方法可用 `server_id=` 覆盖这一次调用的服务节点；省略或传 `None` 时使用客户端的 `server_id`，覆盖值不会更改客户端默认值。interface ID 和资料参数由调用者提供，连接配置不决定资料是否有权限或支持某个返回形式，参见 {doc}`底层 MUSIC 接口 </guide/low-level/index>`。

指定的 INI 路径不存在时，构造函数抛出 `RuntimeError`；缺少 `[Pb]` 或需读取的字段会产生 `configparser` 异常，非整数端口/超时会产生 `ValueError`。底层 `config=` 传入 YAML 路径不会调用加载函数，通常会产生 `TypeError`。这些是请求前的本地错误，不会被包装为响应对象。完整构造参数与方法见 {doc}`客户端参考 </reference/client>`；服务错误的兼容返回约定见 {doc}`MUSIC 兼容性清单 </reference/music-compatibility>`。
