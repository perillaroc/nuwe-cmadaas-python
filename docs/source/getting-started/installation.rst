安装
====

使用 Python 3.11 或更新版本。发行包名是 ``nuwe-cmadaas``，Python 导入名是
``nuwe_cmadaas``。安装依赖需要访问包源；安装完成后，快速入门无需账号或外部网络。

从源码安装并运行教程
--------------------

快速入门使用仓库中的 ``examples/_support/`` 辅助模块，因此请取得完整源码。
这些模块不随主库的 wheel 分发，也无需另行安装旧的示例包。

.. code-block:: bash

    git clone https://github.com/perillaroc/nuwe-cmadaas-python.git
    cd nuwe-cmadaas-python
    python -m venv .venv

Linux、macOS 或 WSL 中激活环境：

.. code-block:: bash

    source .venv/bin/activate

Windows PowerShell 中激活环境：

.. code-block:: powershell

    .\.venv\Scripts\Activate.ps1

随后在仓库根目录安装主库并确认公开函数可导入：

.. code-block:: bash

    python -m pip install -e .
    python -c "import nuwe_cmadaas as n; print(n.retrieve_obs_station.__name__)"

最后一条命令应输出 ``retrieve_obs_station``。运行时依赖（包括 pandas）会随主库
安装；运行快速入门的 Python 代码无需 Sphinx、Click 或测试依赖。
接下来阅读 :doc:`快速入门 <quickstart>`，在同一环境和仓库根目录运行第一个高层调用。

只安装发行包
------------

在已有 Python 虚拟环境中使用发布版本：

.. code-block:: bash

    python -m pip install nuwe-cmadaas

此方式适合在自己的程序中调用主库 API。要复现文档的合成数据示例，请使用上面的
源码安装步骤。真实服务调用另需服务网络、账号及资料权限，配置入口见
:doc:`配置介绍 <../guide/configuration/index>`。

构建可执行文档
--------------

如需在本地构建本站并执行教程，在源码仓库根目录使用 uv 安装文档依赖：

.. code-block:: bash

    uv sync --group docs
    uv run --group docs sphinx-build -b html -E -a -W --keep-going docs/source docs/build/html

构建结果位于 ``docs/build/html/index.html``。Jupyter 内核需要本机 socket 通信；
教程通过注入模拟客户端获取合成数据。文档维护约定见仓库 ``docs/README.md``。
