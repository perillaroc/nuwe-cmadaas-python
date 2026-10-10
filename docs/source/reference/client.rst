底层客户端参考
==============

根包与 ``nuwe_cmadaas.music`` 均导出 CMADaaSClient；构造器、create_connect 和
九个 MUSIC 方法的签名与参数下文从实现生成。配置与选项见 :doc:`configuration`，
完整响应字段见 :doc:`responses`，错误类别见 :doc:`exceptions`。

.. list-table:: 方法、返回与指南
   :header-rows: 1

   * - 方法
     - 返回
     - 指南
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_array2D`
     - :py:class:`~nuwe_cmadaas.music.Array2D`
     - :doc:`表格 <../guide/low-level/tables>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridArray2D`
     - :py:class:`~nuwe_cmadaas.music.GridArray2D`
     - :doc:`数组格点 <../guide/low-level/grids>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridScalar2D`
     - :py:class:`~nuwe_cmadaas.music.GridScalar2D`
     - :doc:`标量格点 <../guide/low-level/grids>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridVector2D`
     - :py:class:`~nuwe_cmadaas.music.GridVector2D`
     - :doc:`矢量格点 <../guide/low-level/grids>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_fileList`
     - :py:class:`~nuwe_cmadaas.music.FilesInfo`
     - :doc:`清单 <../guide/low-level/file-list>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_downFile`
     - :py:class:`~nuwe_cmadaas.music.FilesInfo`，写目标目录
     - :doc:`下载 <../guide/low-level/downloads>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_saveAsFile`
     - :py:class:`~nuwe_cmadaas.music.FilesInfo`，写指定目标
     - :doc:`格式化保存 <../guide/low-level/save-as-file>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_serializedStr`
     - str
     - :doc:`序列化 <../guide/low-level/serialization>`
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_dataBlock`
     - :py:class:`~nuwe_cmadaas.music.DataBlock`
     - :doc:`数据块 <../guide/low-level/data-block>`

使用原生 interface_id/params，客户端不将高层选择器翻译为服务参数。
server_id 覆盖单次请求，不修改默认节点。返回格式必须与具体接口/资料匹配；
DataBlock 当前没有已验证真实服务组合，每次方法调用仍发出能力警告。
保留的参数修改、兼容文本、文件副作用及异常边界见 :doc:`music-compatibility`。

签名与参数
----------

.. currentmodule:: nuwe_cmadaas.music

.. autoclass:: CMADaaSClient
   :members:
   :special-members: __init__
   :undoc-members:
