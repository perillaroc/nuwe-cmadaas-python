参考
====

本部分收录公开 API 签名、响应/配置/异常类型与当前 MUSIC 契约。
按任务使用的可执行示例见 :doc:`指南 <../guide/index>`；
查询登记、案例实现与历史真实服务验证分别展示于 :doc:`完整支持矩阵 <support-matrix>`。

根包 ``nuwe_cmadaas`` 重导出八个高层入口、CMADaaSClient、七种响应/文件类型、
CMADaasConfig、MusicError 和八种结构化异常。高层也由 obs/model 导出；
music 另导出三个配置/客户端辅助函数。定义模块中的 RequestInfo、ResponseData、
AuthItem、ServerItem 和 UnsupportedQueryError 的导入位置在对应页面说明。

.. toctree::
   :maxdepth: 1

   high-level
   client
   responses
   configuration
   exceptions
   support-matrix
   music-compatibility
