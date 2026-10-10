文档维护
========

在完整源码仓库根目录使用 Python 3.11 或更新版本。安装文档依赖并执行全部
MyST-NB 教程，以严格模式构建 HTML：

.. code-block:: bash

   uv sync --group docs
   uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html

``-E -a`` 强制重新读取并执行全部页面，``-W`` 将 Sphinx 警告视为失败。
Notebook 使用注入的人工客户端，不读取真实服务配置；Jupyter 内核需要本机
socket 通信。公共 CI 在 Sphinx 主进程和内核中安装 Python socket 审计钩子，
允许本机通信并拒绝外部 DNS、TCP、UDP；实际内核探针须先通过。完整命令见仓库
:download:`docs/README.md <../../README.md>`。该守卫不等同操作系统网络命名空间，
完整外连隔离仍须按独立验收执行。

新增可执行页面
--------------

从仓库的 ``docs/templates/executable-page.md`` 复制模板，在
``docs/simulated-pages.json`` 登记相对 ``docs/`` 的页面路径，再运行：

.. code-block:: bash

   python3 docs/check_simulated_pages.py

该检查还从生产源码读取八个高层函数与九个底层方法，要求每个入口在可见的可执行
单元中有调用。严格构建后运行 ``python docs/check_rendered_pages.py docs/build/html``，
核对专章链接、默认折叠但可展开的准备代码，以及可见的业务代码和输出。

页面使用 MyST-NB 的 Python 单元，准备及客户端注入放在可展开的 ``hide-input``
单元；公开 API 调用和结果放在可见单元；仅校验用断言可用 ``remove-cell``。
每页应可独立执行，并在首个代码单元前链接
:doc:`模拟数据与客户端注入 <../guide/simulated-data>`。辅助模块位于
``examples/_support/``，不随 wheel 分发。若在独立文档树构建，设置
``NUWE_CMADAAS_REPO_ROOT`` 指向本仓库。完整约定见仓库
:download:`docs/README.md <../../README.md>`。

维护指南、参考与矩阵
--------------------

顶层导航依次为 :doc:`开始使用 <../getting-started/index>`、
:doc:`指南 <../guide/index>`、本开发部分和 :doc:`参考 <../reference/index>`。
新业务页面应加入所属 ``index.rst`` 的 toctree，并从相关参考页链接。
API 签名和返回契约应与源码一致；模拟结果应清楚标明数据来源，不能写成在线验证。

:doc:`完整支持矩阵 <../reference/support-matrix>` 在 Sphinx 构建时从
``tests/integration/`` 下的分目录 ``cases.yaml`` 生成，并核对
``INTERFACE_SPECS``、测试节点和指南锚点。新增或修改案例时，更新该目录的清单、
实际测试、对应指南锚点及独立返回断言，再严格构建；无需手工维护第二份矩阵。
在线状态仅按实际服务复测结果逐案修改。示例脚本的维护和旧包迁移见
:doc:`示例 <examples>`。

如需 PDF，可在具备 TeX 工具链的环境先构建 LaTeX，再生成 PDF：

.. code-block:: bash

   uv run --group docs sphinx-build -b latex -E -a -W --keep-going docs/source docs/build/latex
   make -C docs/build/latex all-pdf

旧文档路径保留简短迁移页；修改章节位置时核对旧页面指向和设计记录的链接。
四篇原有设计记录已归入 :doc:`设计记录 <adr/index>`。
