# nuwe-cmadaas-python

![Maturity-Sandbox](https://img.shields.io/badge/Maturity-Sandbox-F9D71C)
![GitHub Release](https://img.shields.io/github/v/release/perillaroc/nuwe-cmadaas-python)
![PyPI - Version](https://img.shields.io/pypi/v/nuwe-cmadaas)
[![Documentation Status](https://readthedocs.org/projects/nuwe-cmadaas-python/badge/?version=latest)](https://nuwe-cmadaas-python.readthedocs.io/zh_CN/latest/?badge=latest)
![GitHub License](https://img.shields.io/github/license/perillaroc/nuwe-cmadaas-python)
![GitHub Action Workflow Status](https://github.com/perillaroc/nuwe-cmadaas-python/actions/workflows/ci.yml/badge.svg)

`nuwe-cmadaas` 是 Python 3.11+ 的 CMADaaS MUSIC 客户端，提供原生 MUSIC 调用与
常用观测、模式资料的高层查询和下载函数。真实服务调用需要可访问的服务、账号和
对应资料权限；源码仓库中的合成示例可在无账号时运行。

## 安装与入门

```bash
python -m pip install nuwe-cmadaas
```

发行包的导入名是 `nuwe_cmadaas`。若要运行无账号快速入门及仓库示例，请取得完整
源码并在仓库根目录安装主项目；辅助模块不在 wheel 中：

```bash
git clone https://github.com/perillaroc/nuwe-cmadaas-python.git
cd nuwe-cmadaas-python
uv sync
uv run python -m examples station
```

[安装说明](docs/source/getting-started/installation.rst)和
[无账号快速入门](docs/source/getting-started/quickstart.md)给出第一个高层调用。
构建后的[完整文档](https://nuwe-cmadaas-python.readthedocs.io/)按开始使用、指南、开发、
参考组织。选择两层接口可看[接口选择指南](docs/source/guide/choosing-api.md)；
完整参数、返回和验证记录分别见 [API 参考](docs/source/reference/index.rst)与
[支持矩阵](docs/source/reference/support-matrix.rst)。

## 示例与配置

仓库的[统一示例集](examples/README.md)覆盖八个高层函数和九个底层方法，默认
使用人工数据，不读取用户配置或访问真实服务。从仓库根目录可列出或运行全部入口：

```bash
uv run python -m examples --list
uv run python -m examples --all
```

需要真实服务时，先根据[高层配置](docs/source/guide/configuration/high-level.md)
或[底层 MUSIC 配置](docs/source/guide/configuration/music-client.md)创建客户端，
核实接口、资料和权限，再按相应指南手动调用。原独立 `example/` 包仍在兼容过渡；
[旧脚本迁移索引](example/MIGRATION.md)列出逐项替代，新项目使用 `examples/`。

## 开发与验证

```bash
uv sync --group test --group docs
uv run pytest tests --disable-socket --strict-markers -q
uv run pytest tests/integration --collect-only -m integration -q --strict-markers
python3 docs/check_simulated_pages.py
uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html
```

默认 pytest 排除在线集成案例；收集命令只检查节点。真实服务测试须单独提供
`CEDARKIT_CONFIG`、`NUWE_CMADAAS_TEST_PROFILE` 和相应权限，并显式选择
`integration` marker。完整运行和结果记录见
[测试开发指南](docs/source/development/testing.md)及
[在线案例说明](tests/integration/README.md)。文档页面与示例维护分别见
[文档开发指南](docs/source/development/documentation.rst)、
[示例开发指南](docs/source/development/examples.rst)和
[文档构建说明](docs/README.md)。原设计记录见
[开发设计记录](docs/source/development/adr/index.rst)。

## License

`nuwe-cmadaas-python` 未做特殊声明部分代码由 Wang Dapeng (CEMC/CMA) 开发，
采用 [Apache License 2.0](LICENSE)。
