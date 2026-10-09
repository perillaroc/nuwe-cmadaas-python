底层 MUSIC 接口
===============

底层 ``nuwe_cmadaas.music.CMADaaSClient`` 直接接收 MUSIC interface ID 和原生参数。
同一个站点查询的两层调用对照见 :doc:`接口选择 <../choosing-api>`；
不需要自己选择 interface 时，可使用 :doc:`高层业务入口 <../high-level/index>`。

INI 文件、连接参数及字典配置的优先级见
:doc:`底层客户端配置 <../configuration/music-client>`。

.. toctree::
   :maxdepth: 1

   tables
   grids
   file-list
   downloads
   serialization
   save-as-file
   data-block

按返回形式选择方法
------------------

下面列出全部 9 个方法，方法名均链接客户端参考。
:doc:`底层表格指南 <tables>` 已展示原生参数、请求状态、字符串数组及 DataFrame 转换；
:doc:`底层格点指南 <grids>` 分别展示数组、标量和矢量的原始响应与 xarray 转换。
:doc:`文件清单 <file-list>` 展示 FilesInfo 元数据；
:doc:`文件下载 <downloads>` 实际写入文件并说明覆盖及批量失败。
:doc:`序列化 <serialization>` 返回原始格式字符串，
:doc:`格式化保存 <save-as-file>` 展示生成文件、参数修改及实际正文。
:doc:`数据块 <data-block>` 展示名称、原始 bytes 与已知格式的内存读取；
其真实服务能力仍待确认。

.. list-table::
   :header-rows: 1

   * - 方法
     - 返回值
     - 使用结果与文件副作用
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_array2D`
     - ``Array2D``
     - 先检查 ``request`` / ``ok``，读取 ``element_names`` / ``data``，
       见 :doc:`表格全流程 <tables>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridArray2D`
     - ``GridArray2D``
     - ``to_xarray()`` 转为二维 ``DataArray``，见 :doc:`数组格点 <grids>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridScalar2D`
     - ``GridScalar2D``
     - ``to_xarray()`` 转为二维标量场 ``DataArray``，见 :doc:`标量格点 <grids>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_gridVector2D`
     - ``GridVector2D``
     - ``to_xarray()`` 转为包含 U/V 分量的 ``Dataset``，见 :doc:`矢量格点 <grids>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_fileList`
     - ``FilesInfo``
     - 只查询 ``files_info`` 清单，不下载；每项为 ``FileInfo``，
       见 :doc:`文件清单 <file-list>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_downFile`
     - ``FilesInfo``
     - 查询清单并下载到 ``file_dir``，可用 ``overwrite`` 控制已有文件覆盖，
       见 :doc:`文件下载 <downloads>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_saveAsFile`
     - ``FilesInfo``
     - 按 ``data_format`` 保存并下载到 ``file_name``；会补充或修改 ``params``，
       见 :doc:`格式化保存 <save-as-file>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_dataBlock`
     - ``DataBlock``
     - 读取 ``data_name`` 与 ``data``，数据类型为 bytes，不会自动写成文件，
       见 :doc:`数据块指南 <data-block>`。
   * - :py:meth:`~nuwe_cmadaas.music.CMADaaSClient.callAPI_to_serializedStr`
     - ``str``
     - 按服务支持的 ``data_format`` 返回原始字符串，也可能返回兼容错误字符串，
       见 :doc:`序列化 <serialization>`。

格点转换使用 ``latitude/longitude`` 坐标，数组和标量场返回 ``DataArray``，
矢量场返回 ``Dataset``。``FilesInfo`` 不能当成 DataFrame 或高层 ``list[Path]``；
其 ``files_info`` 项包含 ``file_name``、``file_url``、``size`` 等文件信息。

interface、参数与能力边界
--------------------------------

各方法使用 ``interface_id``、``params`` 和可选 ``server_id``；保存或序列化方法
另有 ``data_format``，下载方法还需目标目录或文件名。``params`` 使用原生键名，
例如 ``dataCode``、``times``、``timeRange``、``fcstEle``，不要直接放高层的
``data_code``、``start_time`` 或 ``forecast_time``。

方法与 interface 的返回格式必须匹配。客户端提供某个方法，不代表每个 interface
和资料都支持它；需逐接口核对服务目录和权限。``callAPI_to_dataBlock`` 当前尚无
已验证的真实服务接口，其本地解码能力有合成数据验证，不能据此宣称在线可用。

``callAPI_to_serializedStr`` 会在缺少 ``dataFormat`` 时补入格式；
``callAPI_to_saveAsFile`` 还会设置 ``savepath``。调用者提供的 ``dataFormat``
不覆盖，重复使用参数字典前应留意这些修改。下载调用返回 ``FilesInfo`` 并可能写文件，
只需查看清单时选择 ``callAPI_to_fileList``。

响应状态与转换
--------------

protobuf 方法把服务或传输错误放在响应的 ``request.error_code`` 和
``request.error_message`` 中，``ok`` 表示错误码为零。调用后应先判断状态，
或用 ``raise_for_error(interface_id=..., params=...)`` 转成结构化异常，再进行转换。
提供转换实现的响应在 ``to_pandas()`` / ``to_xarray()`` 时检查状态；
DataBlock 没有这些转换实现，继承方法抛 NotImplementedError，应显式检查请求状态。
成功空结果与错误响应不同。

字符串方法没有上述响应对象属性，按兼容契约可能返回错误文本。
完整签名见 :doc:`客户端参考 <../../reference/client>`，错误和参数约定见
:doc:`MUSIC 兼容性清单 <../../reference/music-compatibility>`。
字符串数值化、单位/缺测与 attrs 见 :doc:`使用返回结果 <../results>`；
响应错误上下文及本地异常见 :doc:`错误处理 <../errors>`。
