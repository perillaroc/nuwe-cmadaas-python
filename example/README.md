# 旧示例包兼容入口

新示例统一位于 [examples/README.md](../examples/README.md)。从完整源码仓库根目录
安装主项目即可运行，不需要安装独立示例包或 Click：

```bash
uv sync
uv run python -m examples --list
uv run python -m examples station
uv run python -m examples --legacy music/station_element_statistics/station_element_statistics_array_2d.py
```

这些新入口默认只运行人工数据并检查结果，下载/保存使用临时目录且完成后清理。
[58 个旧脚本的逐项去向](MIGRATION.md) 保留原生 interface、响应方法与四种格式。
旧的 `grid_verctor_2d.py` 拼写映射到 `vector_grid`；文件名含 rect 的数组例实际是
全域 interface，另有独立矩形格式化场景。空高层占位的替代是
`uv run python -m examples model-grid`，原空模块为旧导入兼容继续保留。

## 仍需要原路径的使用者

旧 `nuwe_cmadaas_example.*` 导入和 Click 脚本继续保留。仅为兼容这些路径时，从
仓库根目录安装主项目及旧包：

```bash
python -m pip install .
python -m pip install ./example
python -m nuwe_cmadaas_example.music.station_info_search.station_info_search_array_2d --help
```

原模块或脚本的 Click 参数仍由旧代码解释；新 `--legacy` 只按路径选择离线替代，
不接收 `--user/--password/--server-id/--client-config` 等旧认证选项。
原脚本实际运行会访问真实服务，且保留历史实现，包括部分 2019～2021 固定日期和
旧资料配置。新离线入口不会执行这些原脚本；真实服务替换请使用统一示例中的
显式配置与运行时日期方式，并先确认资料、参数、返回形式和下载规模。

## 配置与输出迁移

底层 INI 示意已整理到 [新配置模板](../examples/config/client.config.example)，
本目录 [兼容副本](config/client.config.example) 同步保留。需手动填入服务连接选项，
认证另由 `user/password` 或 CedarKit YAML 提供；模板不含真实凭据。
旧 `util.py` 仍从安装的旧包附近查找 `config/client.config` 并创建 `output/`，不用于
新示例。推荐原生辅助 `make_live_music_client("/path/to/cedarkit.yaml")` 只读取明确
路径，并通过 `make_live_params()` 计算日期后手动注入；YAML 与 MUSIC INI 不能互换。
新离线保存/下载自动清理临时目录；真实输出路径由调用者显式提供并检查数量/大小。

## 保留和退出条件

本次核查仓库发布配置仍只构建主包，本地可见引用不足以判断外部安装使用情况。
`pyproject.toml` 和旧包至少保留到本轮示例迁移与 E06 分发边界验收完成；不会因为
替代脚本离线通过就自动撤销旧发行入口。退出还需要核对外部依赖/发布使用证据、
完成迁移通知与必要的兼容期，并确认独特场景和格式的替代验证状态。
服务未验证或缺权限的场景不能以人工成功代替在线验收。若仍有稳定安装入口需求，
继续保留兼容包；满足退出条件后再单独移除打包配置与旧占位/辅助文件。
