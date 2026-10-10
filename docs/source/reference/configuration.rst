配置类型与客户端选择
====================

使用步骤和占位配置见 :doc:`高层配置 <../guide/configuration/high-level>` 与
:doc:`MUSIC INI/构造参数 <../guide/configuration/music-client>`。
完整客户端构造签名见 :py:class:`nuwe_cmadaas.music.CMADaaSClient`；
本页的辅助函数只选择/初始化客户端或读本地文件，不证明认证和服务可用。

导出位置
--------

CMADaasConfig 从根包、nuwe_cmadaas.music 和 nuwe_cmadaas.config 可导入；
拼写为 **CMADaasConfig**，与 CMADaaSClient 的大小写不同。
AuthItem/ServerItem 在 nuwe_cmadaas.config，未从根包或 music 导出。
load_cmadaas_config 在 config 和 music；create_client/get_or_create_client
在 music，三者均不是根包导出。

配置字典类型
------------

.. currentmodule:: nuwe_cmadaas.config

.. autoclass:: AuthItem

.. list-table:: AuthItem 必需键
   :header-rows: 1

   * - 键
     - 注解
     - 含义
   * - user
     - str
     - 账号
   * - password
     - str
     - 密码

.. autoclass:: ServerItem

.. list-table:: ServerItem 必需键
   :header-rows: 1

   * - 键
     - 注解
     - 含义
   * - music_server
     - str
     - 主机或 IP，不含协议/API 路径
   * - music_port
     - int
     - 服务端口
   * - music_ServiceId
     - int
     - 节点 ID；客户端显式 server_id/INI 可使用字符串
   * - music_connTimeout
     - int
     - 连接超时，秒
   * - music_readTimeout
     - int
     - 读取超时，秒

.. autoclass:: CMADaasConfig

CMADaasConfig 必需键为 auth: AuthItem、server: ServerItem。
三者是 TypedDict，运行时构造结果为普通 dict，注解不会校验必需字段、值类型、
权限或凭据，也不会自动展开环境变量。YAML 文件顶层为 cmadaas，传给客户端的
配置字典是取出的 auth/server 节点，不再带 cmadaas 包装。

配置加载
--------

.. autofunction:: load_cmadaas_config

file_path 为显式文件路径时使用该路径；为 None 时，只要 CEDARKIT_CONFIG 存在
就使用它（包括空值），否则使用 Path.home()/".config/cedarkit.yaml"。
各来源不合并；文件缺失或解析错误不回退。相对路径从当前工作目录解析，字符串
中的 ~ 不自动展开。文件读取返回 YAML 的 cmadaas 值，不做运行时结构校验。
FileNotFoundError、KeyError、TypeError 或 YAML 解析异常可以直接传播，
不会统一转为 :py:exc:`~nuwe_cmadaas.music.CMADaaSConfigurationError`。

客户端创建与注入
----------------

.. currentmodule:: nuwe_cmadaas.music

.. autofunction:: create_client

config 是必传参数，没有默认值，但可显式传 None。
dict 直接传入 CMADaaSClient(config=...)；其他值按 YAML 路径/None 查找加载。
此辅助函数没有 session、transport、日志或重试参数，需定制时直接构造客户端。

.. autofunction:: get_or_create_client

client 非 None 则原样返回，忽略 config 并在其非 None 时记录警告，不读文件；
client 为 None 则调用 create_client(config)。注入只决定客户端选择，仍会执行
高层函数自身的参数校验。

MUSIC INI 与构造参数
--------------------

CMADaaSClient(config=...) 只接收内层字典，config_file=... 才读取 MUSIC INI。
不自动查找 client.config，也不读取 CEDARKIT_CONFIG。连接字段仅在值为 None
时补齐，顺序为显式参数 → INI → 字典；认证为显式 user/password → 字典 auth，
INI 不读取认证。INI [Pb] 字段与 ServerItem 同名，port/timeout 按整数解析，
节点按字符串读取。显式超时允许浮点数；缺字段不会自动补业务默认值。

session/transport 互斥，调用者管理 session 生命周期；log_policy、max_retries、
retry_backoff 是构造参数，YAML/INI 同名键不设置这些选项。
create_connect(user,password) 仅替换认证并重建本地连接，不重新读配置或登录。
配置错误与 strict 无关，更多错误边界见 :doc:`exceptions` 和
:doc:`错误指南 <../guide/errors>`。
