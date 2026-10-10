# E02 真实服务验收：2026-10-10

本轮在本地 WSL、Python 3.14.3 下使用默认 CedarKit 凭据文件和临时私有测试 profile，直连 `NMIC_MUSIC_CMADAAS` 服务节点；没有将凭据、签名 URL 或私有 profile 写入仓库。下列结果为本轮实际执行结果，不把历史通过、收集成功或跳过计入本轮成功。

## 结果与边界

- 88 条清单案例全部有本轮结果：**75 通过、3 失败、10 跳过**；本轮在线成功验证率为 **75/88（85.2%）**。此外，6 个 REPS 错误码专项节点均通过。
- 3 个失败均为 REPS 格点：`MGF-017` 返回服务码 `-9002`；`MGF-017-member-10` 和 `MGF-018` 返回全缺测格点。相同运行时日期的定向复测再次得到相同结果。服务资料与时次需核查，尚无证据表明本地请求构造错误。
- 10 个跳过案例保留原有历史 `online_status` 和历史验证时间；清单另记 `e02_2026_10_10_result: skipped` 与明确原因。它们均未发起本轮服务请求。
- 因此清单当前历史状态为 75 `passed`、11 `failed`、2 `implemented-unverified`；其中 8 个历史失败与 2 个未验证案例在本轮跳过。下表的跳过行所列资料代码仅为示例 profile 值，本轮没有以这些代码发起请求，也不代表账号已有权限。
- 站点以本机前一天（10 月 9 日）为基准；地面格点、高空表格和模式分析使用 10 月 7 日 00 时，模式预报、模式点、模式文件及 MUSIC 使用 10 月 7 日 06 时；地面和高空文件以两天前（10 月 8 日）为基准。气候值不传时间，latest 专项用相对时长。所有时次均由运行时 fixture 生成。
- 普通文件批次用 64 MiB 上限。`MF-009` 使用 1.5 GiB 上限并通过；`MF-010`、`MF-012`、`MF-019` 的预查询各返回一个 1,722,610,002 字节文件，先被 1.5 GiB 上限拦截，调整私有 profile 至 1.8 GB 后分别实际下载通过。下载均写入 pytest 临时目录；`MF-009` 及后三例均要求单文件。

## 逐案结果

| 案例 | family | 本轮结果 | 资料代码 | 说明 |
| --- | --- | --- | --- | --- |
| `MF-003` | `model_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MF-004` | `model_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MF-008` | `model_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MF-009` | `model_file` | passed | `NAFP_GRAPESREPS_FOR_FTM_CHN` | 服务调用与案例断言通过 |
| `MF-010` | `model_file` | passed | `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN` | 服务调用与案例断言通过 |
| `MF-012` | `model_file` | passed | `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN` | 服务调用与案例断言通过 |
| `MF-019` | `model_file` | passed | `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN` | 服务调用与案例断言通过 |
| `MFL-001` | `model_file_latest` | passed | `NAFP_ANA_FTM_GRAPES_GFS_NEHE` | 服务调用与案例断言通过 |
| `MGF-002` | `model_grid_forecast` | skipped | `NAFP_FOR_SC_GRAPESBCGZ_9KM_CHN` | Paused pending another catalog-supported NAFP numerical forecast dataset; historical -3001 retained. |
| `MGF-008` | `model_grid_forecast` | passed | `NAFP_GRAPES_MESO_FOR_3KM` | 服务调用与案例断言通过 |
| `MGF-010` | `model_grid_forecast` | skipped | `NAFP_FOR_SC_GRAPESBCGZ_9KM_CHN` | Paused pending another catalog-supported NAFP numerical forecast dataset; historical -3001 retained. |
| `MGF-016` | `model_grid_forecast` | passed | `NAFP_GRAPES_MESO_FOR_3KM` | 服务调用与案例断言通过 |
| `MGF-017` | `model_grid_forecast` | failed | `NAFP_GRAPESREPS_FOR_FTM_CHN` | 服务 `-9002`；定向复测一致 |
| `MGF-017-member-10` | `model_grid_forecast` | failed | `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN` | 全缺测格点；定向复测一致 |
| `MGF-018` | `model_grid_forecast` | failed | `NAFP_GRAPESREPS_FOR_FTM_DIS_CHN` | 全缺测矩形格点；定向复测一致 |
| `MGA-005` | `model_grid_analysis` | passed | `NAFP_GRAPES_MESO_ANA_3KM` | 服务调用与案例断言通过 |
| `MGA-013` | `model_grid_analysis` | passed | `NAFP_GRAPES_MESO_ANA_3KM` | 服务调用与案例断言通过 |
| `MP-001` | `model_point` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MP-001-multi-point` | `model_point` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MP-002` | `model_point` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MP-003` | `model_point` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `MP-004` | `model_point` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLT-001` | `music_array2d` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLG-001` | `music_grid_array2d` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLG-002` | `music_grid_scalar2d` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLG-003` | `music_grid_vector2d` | passed | `NAFP_ANA_FTM_GRAPES_GFS_NEHE` | 服务调用与案例断言通过 |
| `LLF-001` | `music_file_list` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLF-002` | `music_down_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLS-001` | `music_save_as_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLS-002` | `music_save_as_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLS-003` | `music_save_as_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLS-004` | `music_save_as_file` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLR-001` | `music_serialized_str` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLR-002` | `music_serialized_str` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLR-003` | `music_serialized_str` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLR-004` | `music_serialized_str` | passed | `NAFP_FOR_FTM_GRAPES_CFSV2_NEHE` | 服务调用与案例断言通过 |
| `LLB-001` | `music_data_block` | skipped | `—` | No cataloged RetDataBlock interface, authorized data code, and positive recent sample. |
| `OF-002` | `obs_file` | passed | `SURF_CMPA_FRT_5KM_10MIN` | 服务调用与案例断言通过 |
| `OF-003` | `obs_file` | passed | `SURF_CMPA_FRT_5KM_10MIN` | 服务调用与案例断言通过 |
| `OF-009` | `obs_file` | skipped | `SURF_PRODUCT_PART2_FILE_TAB` | The reference account lacks an authorized station-file data code for this interface. |
| `OFL-001` | `obs_file_latest` | passed | `SURF_CHN_MUL_HOR_N` | 服务调用与案例断言通过 |
| `OG-002` | `obs_grid` | passed | `SURF_CMPAS_CHN_1KM_RT` | 服务调用与案例断言通过 |
| `OG-005` | `obs_grid` | passed | `SURF_CMPAS_CHN_1KM_RT` | 服务调用与案例断言通过 |
| `OS-002` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-002-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-003` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-004` | `obs_station` | passed | `SURF_CLI_CHN_HOR_TEM_1991_2020` | 服务调用与案例断言通过 |
| `OS-007` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-007-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-007-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-008` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-008-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-009` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-009-day-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-009-day-scalar` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-010` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-012` | `obs_station` | passed | `SURF_CHN_MUL_HOR_N` | 服务调用与案例断言通过 |
| `OS-014` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-014-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-015` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-017` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-017-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-018` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-020` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-020-time-list` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OS-021` | `obs_station` | passed | `SURF_CHN_MUL_HOR` | 服务调用与案例断言通过 |
| `OSL-001` | `obs_station_latest` | passed | `SURF_CHN_MUL_HOR_N` | 服务调用与案例断言通过 |
| `OU-002` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-003` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-008` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-009` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-010` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-011` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-014` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-015` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-016` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OU-017` | `obs_upper` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OUG-008` | `obs_upper_gps` | skipped | `UPAR_CHN_GPSMET_MUL` | The reference account lacks GPS upper-air data access; historical -4001 retained. |
| `OUG-010` | `obs_upper_gps` | skipped | `UPAR_CHN_GPSMET_MUL` | The reference account lacks GPS upper-air data access; historical -4001 retained. |
| `OUG-011` | `obs_upper_gps` | skipped | `UPAR_CHN_GPSMET_MUL` | The reference account lacks GPS upper-air data access; historical -4001 retained. |
| `OUL-009` | `obs_upper_light` | skipped | `UPAR_ADTD_CHN_LIS` | The reference account lacks Light upper-air data access; historical -4001 retained. |
| `OUA-001` | `obs_upper_ard` | skipped | `UPAR_ARD_G_MUT_AMD` | A controlled recent Ard sample with finite flight height inside the requested range is needed; historical 999999 sentinel retained. |
| `OUA-002` | `obs_upper_ard` | skipped | `UPAR_ARD_G_MUT_AMD` | A controlled recent Ard sample in the requested rectangle and time is needed; historical no-record result retained. |
| `OULAT-001` | `obs_upper_latest` | passed | `UPAR_CHN_MUL_FTM` | 服务调用与案例断言通过 |
| `OUF-002` | `obs_upper_file` | passed | `UPAR_WPR_STATUS` | 服务调用与案例断言通过 |
| `OUF-003` | `obs_upper_file` | passed | `UPAR_WPR_STATUS` | 服务调用与案例断言通过 |
| `OUF-007` | `obs_upper_file` | passed | `UPAR_WPR_STATUS` | 服务调用与案例断言通过 |
| `OUF-009` | `obs_upper_file` | passed | `UPAR_WPR_STATUS` | 服务调用与案例断言通过 |

## REPS 负向专项

这 6 个参数化节点不在 `cases.yaml` 的 88 条注册案例内；本轮均实际连接服务并通过预期错误码断言：

- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_CHN-extra_kwargs0--1]`：passed。
- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_CHN-extra_kwargs1--9002]`：passed。
- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_DIS_CHN-extra_kwargs2--9002]`：passed。
- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_DIS_CHN-extra_kwargs3--3001]`：passed。
- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_DIS_CHN-extra_kwargs4--9002]`：passed。
- `test_reps_service_error_codes[NAFP_GRAPESREPS_FOR_FTM_DIS_CHN-extra_kwargs5--9002]`：passed。

## 执行批次

| 批次 | 开始时间（+08:00） | 结果 |
| --- | --- | --- |
| smoke | 2026-10-10T13:17:48.159387+08:00 | 11 passed, 1 failed |
| extended（64 MiB） | 2026-10-10T13:21:42.809786+08:00 | 62 passed, 20 skipped |
| full-grid | 2026-10-10T13:25:17.487569+08:00 | 4 passed, 2 failed |
| REPS file（1.5 GiB） | 2026-10-10T13:26:07.373904+08:00 | 1 passed, 3 preflight cap failures |
| REPS file（1.8 GB） | 2026-10-10T13:27:17.639562+08:00 | 3 passed |
| REPS grid retry | 2026-10-10T13:35:23.049512+08:00 | 3 failed，结果与首轮一致 |

运行入口为 `pytest tests/integration -m 'integration and smoke'` 与 `-m 'integration and extended'`；全域格点、大文件和失败复测使用精确节点。所有批次均加 `--strict-markers --tb=no --show-capture=no`，并移除代理环境变量以直连服务。每批 JUnit XML 位于私有临时目录，仅用于本次逐节点对账。

## 待补齐条件

- 核对 REPS 控制成员在 10 月 7 日 06 时的资料范围，以及扰动成员 10 该时次的有效值；如资料周期或要素配置变化，应先核实目录与可用资料，再调整测试 profile 或明确记录服务缺测。
- 为暂停的两个 NAFP 接口取得另一种目录支持且已授权的数值预报资料；为 GPS、Light、站号文件与 DataBlock 取得对应权限或目录证据；为 Ard 找到近期有效飞行高度/区域样本。没有这些条件时，跳过不构成真实服务通过。

