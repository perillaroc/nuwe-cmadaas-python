# 高层配置：CedarKit YAML 与客户端注入

`nuwe_cmadaas.obs` 和 `nuwe_cmadaas.model` 的高层查询、下载函数共用 `config=` 与 `client=`。本页说明如何为真实服务提供连接与认证信息；示例中的账号、地址和路径都是占位值，应换成实际配置。Python 代码块供手动运行，文档构建不执行真实请求。

无账号的调用方式见 {doc}`无账号快速入门 </getting-started/quickstart>`，其人工数据和注入机制见 {doc}`模拟数据与客户端注入 </guide/simulated-data>`。

## YAML 文件结构

将配置保存为 `cedarkit.yaml`。文件顶层必须有 `cmadaas`；加载函数取出该节点，再传给客户端：

```yaml
cmadaas:
  auth:
    user: YOUR_USER
    password: YOUR_PASSWORD
  server:
    music_server: YOUR_MUSIC_HOST
    music_port: 80
    music_ServiceId: 0
    music_connTimeout: 10
    music_readTimeout: 60
```

字段名与大小写按上例保留，尤其是 `music_ServiceId` 和两个超时字段。配置中的值不会自动从环境变量展开，`YOUR_*` 必须替换后才能请求真实服务。

| 字段 | 用途 |
| --- | --- |
| `auth.user` / `auth.password` | CMADaaS 账号与密码，使用字符串 |
| `server.music_server` | MUSIC 服务主机或 IP，不含 `http://` 和 API 路径 |
| `server.music_port` | 服务端口，使用整数 |
| `server.music_ServiceId` | 默认服务节点 ID，YAML 常用整数；由服务部署提供 |
| `server.music_connTimeout` | 连接超时，秒 |
| `server.music_readTimeout` | 读取超时，秒 |

通过 YAML 创建客户端时，请提供全部字段；库没有为缺失的配置项补业务默认值。连接超时与读取超时分别传给 HTTP transport，不是一次请求的总时长上限。

## 配置路径的查找顺序

未提供 `client=` 时，高层函数按以下顺序选择配置来源：

1. `config=` 是字典：直接使用该配置对象。
2. `config=` 是字符串或 `pathlib.Path`：读取指定 YAML 文件。
3. `config=None` 且设置了 `CEDARKIT_CONFIG`：读取该环境变量指定的文件。
4. `config=None` 且未设置该变量：读取 `Path.home() / ".config/cedarkit.yaml"`。

这些来源不会相互合并。指定的文件缺失或内容错误时直接报错，不会退回环境变量或默认文件；环境变量即使为空也视为已设置。相对路径以运行进程的当前工作目录为准，字符串中的 `~` 不自动展开，可使用 `Path(...).expanduser()`。

Linux、macOS 或 WSL 中可设置：

```bash
export CEDARKIT_CONFIG=/path/to/cedarkit.yaml
```

Windows PowerShell 中可设置：

```powershell
$env:CEDARKIT_CONFIG = "C:\path\to\cedarkit.yaml"
```

## 在高层调用中指定 YAML

以下地面站点调用使用运行日期的前一天；请换成账号可访问的真实资料代码、站号和配置路径后执行：

```python
from pathlib import Path
import pandas as pd
from nuwe_cmadaas.obs import retrieve_obs_station

table = retrieve_obs_station(
    "SURF_CHN_MUL_HOR",
    elements="Station_Id_C,Lat,Lon,TEM",
    station="YOUR_STATION_ID",
    time=pd.Timestamp.now().normalize() - pd.Timedelta(days=1),
    config=Path("/path/to/cedarkit.yaml"),
    strict=True,
)
```

如果已经设置环境变量或使用默认文件，可省略 `config=`。其他资料类别的日期规则见 {doc}`测试与动态时间 </development/testing>`；不能将教程的固定合成时间用于真实服务查询。

## 使用配置对象

`CMADaasConfig` 是 `TypedDict`，运行时使用普通字典。对象直接包含 `auth` 和 `server`，**不再包含顶层 `cmadaas`**：

```python
from nuwe_cmadaas.config import CMADaasConfig
from nuwe_cmadaas.music import create_client

cmadaas_config: CMADaasConfig = {
    "auth": {"user": "YOUR_USER", "password": "YOUR_PASSWORD"},
    "server": {
        "music_server": "YOUR_MUSIC_HOST",
        "music_port": 80,
        "music_ServiceId": 0,
        "music_connTimeout": 10,
        "music_readTimeout": 60,
    },
}
client = create_client(cmadaas_config)
```

构造客户端只保存配置并创建本地连接对象，不会登录或发 HTTP 请求。要在高层函数中使用字典，将它传给 `config=cmadaas_config`；也可用 `load_cmadaas_config(path)` 从 YAML 得到相同结构。

## 显式客户端优先

需要复用连接、设置重试/日志选项或使用 MUSIC INI 时，先构造客户端，再传给高层函数：

```python
from nuwe_cmadaas.music import CMADaaSClient

client = CMADaaSClient(
    config=cmadaas_config,
    connection_timeout=5,
    log_policy="redacted",
    max_retries=1,
)
# 在上面的站点调用中，用 client=client 替换 config=...。
```

高层显式提供 `client=` 时直接使用它，不读取 YAML、环境变量或默认路径。同时传入 `config=` 会记录一条忽略配置的警告，不会将该配置合并到客户端中。`client=` 优先只影响客户端选择，公开函数仍会校验查询参数。

`log_policy`、`max_retries`、`session` 等是客户端构造参数；在 YAML 中加入同名字段不会设置这些选项。在高层查询中使用 `config_file=` 也不能选择 INI，参见 {doc}`底层客户端配置 <music-client>`。

## 配置错误与下一步

YAML 路径不存在时抛出 `FileNotFoundError`；语法错误由 YAML 解析器报错；缺少 `cmadaas`、`auth`、`server` 或读取所需字段可能抛出 `KeyError`，节点类型不正确还可能产生 `TypeError`。`TypedDict` 不提供运行时校验，构造成功也不表示地址、凭据或资料权限有效。这些本地配置错误不会因高层 `strict=False` 而变成 `MusicError`；`strict` 控制的是服务响应错误的处理方式。

配置好连接后，从 {doc}`地面站点 </guide/high-level/obs/station>`、{doc}`地面格点 </guide/high-level/obs/grid>` 或 {doc}`文件下载 </guide/high-level/obs/files>` 选择业务入口；完整签名见 {doc}`高层接口参考 </reference/high-level>`。集成测试的资料与案例开关另由 `NUWE_CMADAAS_TEST_PROFILE` 管理，它不参与生产库的配置查找。
