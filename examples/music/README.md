# MUSIC 原生示例

从完整源码仓库根目录运行；仅安装 wheel 不包含这些辅助模块。
脚本使用 `examples/_support/` 的人工 protobuf 和精确 `SyntheticTransport`，
注入真实 `CMADaaSClient`，无需配置或账号。未知请求立即失败，不回退真实网络。

```bash
uv run python -m examples.music.tables
```

`tables.py` 展示原生 interface/params、Array2D 的 request/ok、列名与字符串数组、
`to_pandas()`、实际 dtype/attrs 及副本上的显式数值转换；成功空结果、服务错误和
解码错误分别验证，失败转换抛结构化异常。四次响应均核对关闭状态。
指南 `docs/source/guide/low-level/tables.md` 复用同一客户端工厂与独立结果断言。
真实服务替换仅作为手动代码展示，不在脚本或文档构建中执行。
