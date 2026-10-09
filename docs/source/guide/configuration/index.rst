配置介绍
========

高层查询使用 CedarKit YAML 或配置字典，也可显式注入客户端；底层 MUSIC 客户端
接收连接参数、配置字典或 MUSIC INI。根据调用入口选择对应配置方式：

.. list-table::
   :header-rows: 1

   * - 调用入口
     - 配置方式
     - 指南
   * - ``retrieve_*`` / ``download_*`` 高层函数
     - ``config=`` 为 YAML 路径或 ``CMADaasConfig`` 字典；``client=`` 优先
     - :doc:`高层配置 <high-level>`
   * - ``CMADaaSClient`` 构造函数
     - ``config_file=`` 为 INI 路径；``config=`` 仅接收配置字典；也可直接传连接参数
     - :doc:`底层客户端配置 <music-client>`

高层 ``config=`` 不能使用 MUSIC INI 路径。``CEDARKIT_CONFIG`` 只用于高层 YAML
加载，底层构造函数不会自动读取该环境变量或当前目录的 ``client.config``。
无账号体验请先运行 :doc:`快速入门 <../../getting-started/quickstart>`。

.. toctree::
   :maxdepth: 1

   high-level
   music-client
