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
     - ``(interface_id, params, file_dir, server_id=None, overwrite=True) -> FilesInfo``
   * - ``callAPI_to_dataBlock``
     - ``(interface_id, params, server_id=None) -> DataBlock``
   * - ``callAPI_to_gridScalar2D``
     - ``(interface_id, params, server_id=None) -> GridScalar2D``
   * - ``callAPI_to_gridVector2D``
     - ``(interface_id, params, server_id=None) -> GridVector2D``

错误和参数语义
==============

* protobuf 方法将已处理的服务、传输、解码和下载失败记录在响应 request 中，
  通过 ok/error_code/error_message 检查，或显式 raise_for_error。
  底层没有 strict 参数；本地配置/参数及未处理异常仍可直接抛出，不能保证始终返回对象。
* ``callAPI_to_serializedStr`` 返回服务正文字符串。传输异常保持当前兼容结果
  ``"Error retrieving data"``，网关错误以历史 ``getway error:`` 等文本返回。
  缺 dataFormat 时补入，已有值优先，不做本地格式白名单校验。
  没有 request/ok/attrs；普通业务失败 JSON 可原文返回，可解析不保证成功，
  UTF-8 或其他未预期解析异常可直接抛出。
* ``callAPI_to_saveAsFile`` 会在 ``params`` 中补充 ``dataFormat`` 和
  ``savepath``（调用者已提供的 ``dataFormat`` 不覆盖），失败后修改仍保留。
  file_name=None 在补格式后、改路径前返回 -10001，且不发请求。
  成功只下载清单第一项到指定 file_name，默认覆盖，目标独立于服务 FileInfo 名称。
  成功空清单现有 IndexError；没有 overwrite/strict/本地字节上限参数。
  保存 API 请求不进行读取重试，随后正文下载沿用连接重试策略。
* ``callAPI_to_downFile`` 要求 ``file_dir``，并按照服务返回的文件名下载文件；
  overwrite 默认 True，False 遇已有目标返回 -10004，不读取该文件正文。
  单文件临时写入后替换，后项失败可保留前项文件，没有整批回滚；
  返回仍为 FilesInfo，清单长度不保证成功下载数量，服务 save_path 不改成本地路径。
  合法空清单成功；没有本地总字节或文件数量上限。
* fileList 只读元数据，不下载正文；不把 FilesInfo 转为高层 list[Path]。
  FileInfo.size 保留字符串，HTTP Content-Length 检查不等于核验该元数据大小。
* DataBlock 的 data_name/data 为名称与 bytes，不自动写文件或转换表格/格点。
  非零服务错误也可保留内容，需先检查状态；每次调用发出无已验证真实接口的警告。
  成功空内容或合成响应不作为服务能力证据。
* ``callAPI_to_*`` 保留 MUSIC 原生参数字典的处理方式和既有 URL/签名规则。
  高层 API 的规范化和校验不改变直接底层调用的参数含义。

签名/参数与对象见 :doc:`client`、:doc:`responses`；错误类别与默认/strict
控制流见 :doc:`exceptions` 和 :doc:`错误指南 <../guide/errors>`。
可执行调用由 :doc:`底层指南 <../guide/low-level/index>` 分别覆盖九个方法。

兼容性测试
==========

底层契约测试位于 ``tests/unit/music``，覆盖方法调用、参数处理、protobuf 返回
对象和非零 MUSIC 错误码。新增底层便利能力必须保持这些断言通过；不兼容变化必须
先增加弃用周期和迁移说明。
