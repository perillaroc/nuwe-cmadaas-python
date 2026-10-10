# CMADaaS 集成测试操作说明

从仓库根目录运行以下命令。测试需要 Python 3.11+、可访问的 CMADaaS 服务，以及账号对所选资料代码的权限。普通 `pytest` 默认排除 `integration` marker；在线运行须显式选择。

## 配置

安装测试依赖：

```bash
uv sync --group test
```

认证与服务地址使用 `CEDARKIT_CONFIG` 指向的 CedarKit YAML；未设置时读取 `~/.config/cedarkit.yaml`。其格式由 `src/nuwe_cmadaas/config.py` 读取，例如：

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

服务参数填写账号实际配置；此文件不放入仓库。资料、站号、要素和下载限制另存为私有测试 profile：

```bash
cp tests/integration/profiles.example.yaml /tmp/nuwe-cmadaas-test-profile.yaml
export CEDARKIT_CONFIG=/path/to/cedarkit.yaml
export NUWE_CMADAAS_TEST_PROFILE=/tmp/nuwe-cmadaas-test-profile.yaml
```

编辑复制后的 profile。高层案例须同时把对应 `datasets.<profile_key>.enabled` 和 `cases.<case_id>.enabled` 设为 `true`；底层案例须同时启用 `low_level.<method>.enabled` 和案例开关。`profile_key`、案例 ID、请求参数和当前状态在各目录的 `cases.yaml` 中。资料代码及预期列必须匹配账号权限和服务目录；示例中的 `EXAMPLE_*` 不能直接用于联网查询。清单本身 `enabled: false` 的失败或待验证案例不会因 profile 开关而运行，须先核实该案例的 `reason`、已有的 `run_prerequisite` 及案例定义。

缺认证文件、测试 profile 或已禁用的资料能力会明确 `skip`；已有但无效的认证或 profile 会报错。已启用案例的认证失败、服务错误、意外空结果和断言失败均记为失败，不会转成跳过或成功。

## 日期与资料

所有在线案例在运行时计算日期；不要在 profile 或案例中写固定查询日期。账号只能访问近期数据时，先核对相应资料的发布周期与近期权限。

| 案例类别 | 当前日期规则 |
| --- | --- |
| 地面站点 | 本机日期的前一天 00 时；短区间、全天区间和前一天/当天列表由该基准生成。`OS-004` 的气候值按站号查询，不传时次。 |
| 地面格点、常规/GPS/Light/Ard 高空表格 | 本机日期的三天前 00 时及由此生成的短区间。 |
| 地面与高空文件 | 本机日期的两天前 00 时，或从该时次起一小时的区间。 |
| 模式格点、模式点、模式文件及底层 MUSIC | 本机日期的三天前 06 时；模式文件的时间段案例使用 06～07 时。 |
| latest-time | `OSL-001`、高空 latest 使用相对 1 小时；`OFL-001` 和 `MFL-001` 分别使用 profile 中的 `latest_hours`（示例为 24 和 72 小时）。它们返回时间表格，不能作为文件下载。地面与高空高层 latest 查询仅接受资料代码和相对时长；附加筛选参数在发请求前报 `UnsupportedQueryError`。 |
| REPS 错误码专项 | 负向案例按运行时日期构造未来时次或无效参数，预期得到指定错误码。 |

这些 fixture 使用测试主机的本地时钟。若所选资料在该动态时次没有记录，应核对资料周期、账号可见窗口和清单中的 `profile_key`，再调整测试资料或日期规则并记录原因；不能把无记录当作通过。

示例 profile 优先给模式点、文件及底层 MUSIC 提供 CMA-GFS 资料。MESO 使用正在运行的 3KM 系统；不要改回已停运的 10KM 系统。`MGF-002`、`MGF-010` 仍需其他支持相应接口的 NAFP 数值预报资料；不能用其他资料类型充当替代。

## 选择和运行

只运行离线测试，不访问服务：

```bash
uv run pytest tests --disable-socket --strict-markers -q
```

仅收集在线节点，不读取认证或连接服务：

```bash
uv run pytest tests/integration --collect-only -m integration -q --strict-markers
```

先在私有 profile 中启用一个资料能力及对应案例，再按精确节点运行。例如 `OS-007`：

```bash
uv run pytest 'tests/integration/obs/station/test_station.py::test_registered_case[OS-007]' -m integration -q -ra --strict-markers
```

按 marker 或目录运行：

```bash
uv run pytest tests/integration -m 'integration and smoke' -ra --strict-markers
uv run pytest tests/integration/model/point -m integration -ra --strict-markers
uv run pytest tests/integration -m 'integration and extended' -ra --strict-markers
```

`smoke` 是范围较小的受控案例；`extended` 包括其他案例、全域格点、文件下载及 REPS 负向专项。`-k OS-007` 也可能匹配同名变体，需要精确运行时使用上面的完整 pytest 节点。所有案例默认不启用，不应将整目录运行后的大量 `skip` 计作通过。

## 文件与输出规模

文件类高层案例通过 `callAPI_to_fileList` 对**相同接口和参数**做预查询，再按 `download_limits.max_files`、`download_limits.max_total_bytes` 和资料自身的 `max_files` 限制下载。示例上限为 2 个文件、64 MiB；模式文件 `MF-003`、`MF-004` 用 `limitCnt=1` 限制服务返回数量。预查询无文件、缺 URL/大小、文件数或总字节数超限时，测试在下载前停止；下载后仍检查临时目录中的路径、文件存在及大小。

`LLF-001` 只查文件元数据；`LLF-002` 预查询后下载单个 GFS GRIB2 文件。`LLS-001`～`LLS-004` 各生成一个受 1 MiB 限制的 JSON/XML/text/HTML 小文件。所有在线文件输出写入 pytest 的 `tmp_path`；不在仓库中保存下载结果。

示例的 GFS 单文件案例曾分别约为 28.5 MiB 或 50 MiB，适合默认 64 MiB 上限。2026-10-10 的 `MF-009` 在单文件、1.5 GiB 上限内通过；`MF-010`、`MF-012`、`MF-019` 的文件清单每例为单个 1,722,610,002 字节文件，使用 1.8 GB 私有上限通过。启用前先检查清单中的资料代码、当次清单大小和可用磁盘空间，并只在私有 profile 中调整 `max_total_bytes`。全域格点案例也会占用较多内存，应单独运行。`download_limits.unbounded_download_approved`、`approved_data_scope`、`approval_reason` 不是当前测试使用的下载开关，设置它们不会绕过字节上限。

## 状态与待验证项

各目录 `cases.yaml` 的 `online_status` 是上次核验记录，**不会**随 pytest 运行自动更新：

| 状态 | 含义 |
| --- | --- |
| `passed` | 曾在所记环境、日期和资料下通过；不保证今天仍有资料或权限。 |
| `failed` | 曾联网失败；查看 `reason`、`verification_blocker`、`recommended_data_code` 和 `run_prerequisite`。 |
| `implemented-unverified` | 有可收集案例或离线实现，但该案例尚无可确认的在线成功。 |

2026-10-10 E02 逐案验收的 88 条清单案例为 **75 passed、3 failed、10 skipped**，另有 6 个 REPS 错误码专项节点通过。3 个失败均为本次时次的 REPS 格点结果，定向复测相同；10 个跳过案例保留历史 `online_status`，另记本轮跳过原因。逐案资料代码、运行时间、结果及后续条件见 [E02 验收记录](verification-2026-10-10.md)。`OFL-001` 已用 `SURF_CHN_MUL_HOR_N` 和相对 24 小时窗口验证 `Datetime` 表格。`OF-009` 需要获授权的站号文件资料 `SURF_PRODUCT_PART2_FILE_TAB`；`LLB-001` 的 DataBlock 转换有离线回归，仍缺目录明确声明 `RetDataBlock` 的接口、已授权资料及近期样本。跳过、未验证和历史失败均不计为本轮成功。

在线复测后，应在对应 `cases.yaml` 中按**单个案例**记录状态、资料代码、执行环境和时间、实际结果或失败原因；不可把一个接口或资料的成功推及整组。B16 只提供运行说明；全量实时服务验收由 E02 另行执行。
