# 文档构建

在仓库根目录使用 Python 3.11 或更新版本：

```bash
uv sync --group docs
uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html
```

RST 页面用于 API 参考，MyST-NB Markdown 页面用于可执行教程。配置对 Notebook 使用
`nb_execution_mode = "force"`；构建时需要允许 Jupyter 内核通过本机 socket 通信。
当前逐接口执行教程尚待 C05～D 阶段编写。

`docs/requirements.txt` 与 `pyproject.toml` 的 `docs` 依赖组保持相同的直接依赖。
Read the Docs 按 `.readthedocs.yml` 先安装前者，再安装本项目；该配置仍请求 PDF。
具备 TeX 工具链时，可先构建 LaTeX 源文件，再检查 PDF 输出：

```bash
uv run --group docs sphinx-build -b latex -E -a -W --keep-going docs/source docs/build/latex
make -C docs/build/latex all-pdf
```

PDF 的实际渲染验收属于 E05；后续文档与示例的 CI 检查属于 D22。
