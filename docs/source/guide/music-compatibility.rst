********************
MUSIC 兼容性清单
********************

本页冻结 ``nuwe_cmadaas.music.CMADaaSClient`` 当前公开的 MUSIC 兼容调用。
高层 ``model`` 和 ``obs`` API 可以增加本地参数校验，但不得改变下列底层调用的
方法名、参数名、返回对象或业务错误承载方式。未被高层覆盖的 MUSIC 接口继续通过
这些方法调用。

方法签名
========

所有 ``interface_id`` 都是调用者明确提供的 MUSIC 接口标识，``params`` 是
MUSIC 原生参数字典，``server_id`` 为可选服务节点覆盖值。

.. list-table::
   :header-rows: 1
   :widths: 30 55

   * - 方法
     - 当前签名
   * - ``callAPI_to_array2D``
     - ``(interface_id, params, server_id=None) -> Array2D``
   * - ``callAPI_to_gridArray2D``
     - ``(interface_id, params, server_id=None) -> GridArray2D``
   * - ``callAPI_to_fileList``
     - ``(interface_id, params, server_id=None) -> FilesInfo``
   * - ``callAPI_to_serializedStr``
     - ``(interface_id, params, data_format, server_id=None) -> str``
   * - ``callAPI_to_saveAsFile``
     - ``(interface_id, params, data_format, file_name, server_id=None) -> FilesInfo``
   * - ``callAPI_to_downFile``
     - ``(interface_id, params, file_dir, server_id=None) -> FilesInfo``
   * - ``callAPI_to_dataBlock``
     - ``(interface_id, params, server_id=None) -> DataBlock``
   * - ``callAPI_to_gridScalar2D``
     - ``(interface_id, params, server_id=None) -> GridScalar2D``
   * - ``callAPI_to_gridVector2D``
     - ``(interface_id, params, server_id=None) -> GridVector2D``

错误和参数语义
==============

* ``Array2D``、``GridArray2D``、``FilesInfo``、``DataBlock`` 及其他 protobuf
  响应对象始终返回；MUSIC 业务错误通过 ``result.request.error_code`` 和
  ``result.request.error_message`` 读取，底层调用不因业务错误抛出异常。
* ``callAPI_to_serializedStr`` 返回服务正文字符串。传输异常保持当前兼容结果
  ``"Error retrieving data"``，网关错误以字符串形式返回。
* ``callAPI_to_saveAsFile`` 会在 ``params`` 中补充 ``dataFormat`` 和
  ``savepath``（调用者已提供的 ``dataFormat`` 不覆盖）。``file_name`` 为空时，
  错误仍写入返回对象的 ``request``。
* ``callAPI_to_downFile`` 要求 ``file_dir``，并按照服务返回的文件名下载文件；
  下载失败仍通过返回对象的 ``request`` 报告错误。
* ``callAPI_to_*`` 保留 MUSIC 原生参数字典的处理方式和既有 URL/签名规则。
  高层 API 的规范化和校验不改变直接底层调用的参数含义。

兼容性测试
==========

底层契约测试位于 ``tests/unit/music``，覆盖方法调用、参数处理、protobuf 返回
对象和非零 MUSIC 错误码。新增底层便利能力必须保持这些断言通过；不兼容变化必须
先增加弃用周期和迁移说明。
