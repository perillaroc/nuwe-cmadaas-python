异常与兼容错误返回
==================

可执行控制流见 :doc:`错误指南 <../guide/errors>`；
底层返回约定见 :doc:`music-compatibility`，响应状态方法见 :doc:`responses`。
本页说明当前本地错误分类，不作为全部服务错误码或可重试策略的规范。

兼容返回 MusicError
-------------------

.. currentmodule:: nuwe_cmadaas.music

.. autoclass:: MusicError

根包与 music 均导出该 dataclass，构造参数 code:int/message:str 均必传。
默认 strict=False 的高层失败响应返回它并发出 DeprecationWarning，成功返回
正常数据（包括合法空结果）。MusicError 不是 Exception，没有 ok/request/attrs；
默认真值 True，应使用 isinstance 判断，不能用 if result 判断成功或直接 raise。

结构化基类
----------

.. autoexception:: CMADaaSError

该基类及七个子类从根包与 music 导出，也可从 music.errors 导入。
message 为必传的位置参数，其余上下文仅接受关键字；子类继承相同构造器。

.. list-table:: 异常构造参数与属性
   :header-rows: 1

   * - 名称
     - 默认 / 含义
   * - message
     - 必传；异常主消息，保存于 args[0]
   * - error_code / server_message
     - None；请求错误码和服务文案
   * - interface_id / params
     - None；显式接口和参数上下文，不从 response.metadata 自动推断
   * - request_id / retries
     - None / 0；当前 response.raise_for_error 不填请求 ID 或连接重试统计
   * - cause
     - None；可选底层异常原因；raise_for_error 在有原因时建立异常链

params 的 Mapping/list/tuple 中 password/passwd/pwd/sign/token/authorization
键按大小写不敏感规则递归替换为 <redacted>。这只针对 params，不保证 message、
服务文案、自定义对象或其他日志字符串均被遮盖。str(error) 包含可用的
code/interface/message，但不打印完整 params；使用客户端日志策略控制请求记录。

失败响应的类别
--------------

.. autoexception:: CMADaaSAuthenticationError

.. autoexception:: CMADaaSTransportError

.. autoexception:: CMADaaSDecodeError

.. autoexception:: CMADaaSDownloadError

.. autoexception:: CMADaaSRequestError

.. list-table:: error_from_request 当前映射
   :header-rows: 1

   * - 错误码
     - 类别
   * - -1004
     - :py:exc:`CMADaaSAuthenticationError`
   * - -10001
     - :py:exc:`CMADaaSTransportError`
   * - -10003
     - :py:exc:`CMADaaSDecodeError`
   * - -10004
     - :py:exc:`CMADaaSDownloadError`
   * - 其他非零值
     - :py:exc:`CMADaaSRequestError`

分类依据错误码，不等于故障来源的完整诊断；例如 saveAsFile 目标 None 的
本地错误兼容写为 -10001。业务失败不可通用地替换为空表、空场或空路径列表。

查询与配置类别
--------------

.. autoexception:: CMADaaSQueryError

.. autoexception:: CMADaaSConfigurationError

.. autoexception:: nuwe_cmadaas.interfaces.UnsupportedQueryError

UnsupportedQueryError 继承 CMADaaSQueryError，通过 interfaces 模块导入，
不属于根包/music 的 __all__。未登记组合在网络请求前拒绝；其他非法参数仍可能
直接抛 TypeError/ValueError。CMADaaSConfigurationError 是公开的分类类型，
当前 YAML/INI 加载并未统一抛此类，文件/解析/缺字段错误可直接传播。

错误转换辅助函数
----------------

以下函数从 music.errors 模块导出，未由根包/music 重导出。

.. autofunction:: nuwe_cmadaas.music.errors.error_from_request

根据 RequestInfo 构造并返回对应异常（本函数不抛异常）；显式 cause 参数传入
错误对象，不自动从 request.cause 读取。正常应用可使用 response.raise_for_error，
由后者获取可选 request.cause 并负责抛出/异常链。

.. autofunction:: nuwe_cmadaas.music.errors.handle_response_error

成功响应返回 None；strict=True 的失败调用 response.raise_for_error；默认失败
发出 DeprecationWarning 并返回 MusicError。此函数只处理传入响应的状态，
不捕获参数、配置、转换或文件操作的全部本地异常。
