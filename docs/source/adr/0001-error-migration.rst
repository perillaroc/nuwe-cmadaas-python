错误语义迁移决策
====================

状态
----

已接受（2026-09-15）。

决策
----

高层 API 采用可选严格模式。现有函数新增 ``strict=False`` 参数，默认行为
保持不变：MUSIC 业务错误仍返回 ``MusicError``。调用方传入 ``strict=True``
时，函数在收到错误响应后抛出结构化的 ``CMADaaSError`` 子类。

底层 ``nuwe_cmadaas.music`` 兼容 API 不改变其返回对象和错误承载方式。
响应对象增加 ``ok`` 属性和 ``raise_for_error()`` 方法，二者均为向后兼容的
便利能力。

错误层次
--------

错误类型及用途如下：

* ``CMADaaSConfigurationError``：客户端配置错误；
* ``CMADaaSQueryError``：高层查询错误，包含未支持的查询组合；
* ``CMADaaSTransportError``：连接或传输失败；
* ``CMADaaSAuthenticationError``：认证失败（当前 MUSIC 认证错误码 ``-1004``）；
* ``CMADaaSRequestError``：其他非零 MUSIC 业务错误码；
* ``CMADaaSDecodeError``：响应解码失败；
* ``CMADaaSDownloadError``：文件下载失败。

结构化异常保留错误码、服务端消息、interface id、脱敏参数、请求标识、
重试次数和原始 cause 字段。密码、签名和认证 token 不会进入参数字段的
可见值或异常字符串。

兼容与迁移
----------

``MusicError`` 返回路径在当前主版本继续保留，并以 ``DeprecationWarning``
提示新代码使用严格模式；这不是删除或默认行为切换。下游 ``reki`` 必须
通过 ``isinstance(result, MusicError)`` 及结构化字段判断错误，不得匹配错误
文本。后续主版本如需改变默认行为，必须另行发布迁移说明和弃用周期。

未决范围
--------

本决策只定义高层响应错误的迁移入口。HTTP 状态分类、protobuf 解码异常的
具体捕获策略、重试和下载错误细分在传输层阶段单独实现。
