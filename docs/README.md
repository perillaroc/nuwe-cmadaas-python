# 文档构建

在仓库根目录使用 Python 3.11 或更新版本：

```bash
uv sync --group docs
uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html
```

RST 页面用于 API 参考，MyST-NB Markdown 页面用于可执行教程。配置对 Notebook 使用
`nb_execution_mode = "force"`；构建时需要允许 Jupyter 内核通过本机 socket 通信。
无账号快速入门、两层接口对照、站点、格点和文件下载已有可执行教程；其余逐接口内容在 D 阶段补齐。

## 可执行模拟页面

复制 `docs/templates/executable-page.md` 到 `docs/source/` 下的目标章节，并在
`docs/simulated-pages.json` 的 `pages` 中登记相对 `docs/` 的路径。模板的
`simulated_data: true` 标记、Python kernel、专章链接和代码单元顺序是页面约定。
登记后运行 `python3 docs/check_simulated_pages.py`，检查页面、专章链接和折叠标签。

每页都从本仓库的 `examples/_support/` 导入辅助代码。Notebook 从工作目录向上
查找仓库；若在独立的临时文档树执行，设置 `NUWE_CMADAAS_REPO_ROOT` 为此仓库
根目录。读者应取得完整源码仓库，安装项目的文档依赖，再运行示例；仅安装
`nuwe_cmadaas` wheel 不包含这些辅助代码。

准备和注入步骤放在首个 `hide-input` 单元中，生成的 HTML 应可展开该单元。
公开 API 的导入、实际调用和结果表达式留在普通代码单元中。只供构建校验的
断言可单独用 `remove-cell`；业务错误处理仍要直接展示。每页单独准备客户端，
不得依赖别的页面执行顺序。所有模拟页面须在首个代码单元前，用可见的
`{doc}` 交叉引用链接到“模拟数据与客户端注入”专章。

高层教程在准备单元中用 `FakeClient.register()` 登记精确请求；调用单元保留
公开函数的 `client=client`。底层教程在准备单元中登记 `SyntheticTransport`
的请求和下载 URL，并调用 `make_synthetic_music_client(transport)`；调用单元
直接展示对应的 `callAPI_to_*` 方法及结果。下载页在页面内创建临时目录并
展示相对文件名及大小，不展示随机的绝对路径。

`docs/requirements.txt` 与 `pyproject.toml` 的 `docs` 依赖组保持相同的直接依赖。
Read the Docs 按 `.readthedocs.yml` 先安装前者，再安装本项目；该配置仍请求 PDF。
具备 TeX 工具链时，可先构建 LaTeX 源文件，再检查 PDF 输出：

```bash
uv run --group docs sphinx-build -b latex -E -a -W --keep-going docs/source docs/build/latex
make -C docs/build/latex all-pdf
```

PDF 的实际渲染验收属于 E05；后续文档与示例的 CI 检查属于 D22。
