# 测试与动态时间

以下命令均在源码仓库根目录执行，使用 Python 3.11 或更新版本。

## 离线测试

```bash
uv sync --group test
uv run pytest tests --disable-socket --strict-markers -q
```

`pyproject.toml` 默认排除 `integration` marker，因此这条命令只执行离线测试。
`tests/unit/` 使用人工响应和注入客户端，不需要账号、配置文件或 CMADaaS 网络。
`--disable-socket` 禁止测试建立 socket；可单独运行
`uv run pytest tests/unit --disable-socket --strict-markers -q`。
新增测试应放在对应子系统附近；参数、解码、异常及文件写入的确定性边界优先用离线测试覆盖。

## 在线案例的收集与执行

仅收集节点不会读取账号或连接服务：

```bash
uv run pytest tests/integration --collect-only -m integration -q --strict-markers
```

真实服务测试需要可访问的 CMADaaS、账号权限和私有 profile。
认证与服务地址由 `CEDARKIT_CONFIG` 指向的 CedarKit YAML 提供；未设置时读取
`~/.config/cedarkit.yaml`。案例资料、期望字段和下载上限由
`NUWE_CMADAAS_TEST_PROFILE` 指向的 profile 提供。先复制
`tests/integration/profiles.example.yaml`，替换示意值，并启用资料能力及具体案例。
配置格式、开关、下载规模和精确节点的操作步骤见仓库的
{download}`集成测试说明 <../../../tests/integration/README.md>`。

```bash
uv run pytest 'tests/integration/obs/station/test_station.py::test_registered_case[OS-007]' -m integration -q -ra --strict-markers
uv run pytest tests/integration -m 'integration and smoke' -ra --strict-markers
uv run pytest tests/integration -m 'integration and extended' -ra --strict-markers
```

没有配置或未启用能力时案例会跳过；已启用案例的认证、服务或数据错误应失败。
`smoke` 是小范围场景，`extended` 包含其他组合及较大查询。目录执行后的跳过数
不能计作在线通过。每个案例的登记、测试节点、历史结果和重跑前提可在
{doc}`完整支持矩阵 <../reference/support-matrix>` 中查找；历史 `passed` 不保证
当前资料仍可用。

## 动态时次与记录

在线集成测试按运行时本地日期选择近期资料；固定时间只用于离线合成示例。

| 资料类别 | 当前在线案例的基准时间 |
| --- | --- |
| 地面站点 | 前一天 00 时 |
| 地面格点及常规/GPS/Light/Ard 高空表格 | 三天前 00 时 |
| 地面与高空文件 | 两天前 00 时 |
| 模式格点、模式点、模式文件及底层 MUSIC | 三天前 06 时 |

最新时次查询使用相对时间参数；latest 表格不能作为文件下载。实际服务还须开放所选
资料、时次和账号权限。资料未到齐或权限失败不等于测试通过，也不能把合成日期复制
到在线请求。复测后按单个案例更新所属目录的 `cases.yaml`，记录状态、实际结果或失败
原因、资料代码、环境与时间；不要将同一 interface 的成功推及其他参数组合。
清单维护规则与状态字段见 {doc}`支持矩阵 <../reference/support-matrix>`。
