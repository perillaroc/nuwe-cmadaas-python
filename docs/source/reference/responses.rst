响应对象与输出契约
==================

客户端与高层入口分别见 :doc:`client`、:doc:`high-level`；数值化、单位/缺测、
attrs 和文件读取的可执行说明见 :doc:`结果指南 <../guide/results>`，
错误控制流见 :doc:`错误指南 <../guide/errors>` 和 :doc:`exceptions`。
本页描述当前解码实现，不把默认对象、空成功或本地构造视作真实服务验证。

导入与返回形式
--------------

Array2D、三类 Grid、FilesInfo、FileInfo 和 DataBlock 可从根包或
``nuwe_cmadaas.music`` 导入；共同基类 ResponseData 与 RequestInfo 仅从
``nuwe_cmadaas.music.data`` 导入。MusicError 是兼容返回类，见 :doc:`exceptions`。

.. list-table::
   :header-rows: 1

   * - 响应类型
     - 实现的转换 / 输出
     - 调用指南
   * - :py:class:`~nuwe_cmadaas.music.Array2D`
     - to_pandas() → DataFrame，原始字符串
     - :doc:`表格 <../guide/low-level/tables>`
   * - :py:class:`~nuwe_cmadaas.music.GridArray2D`
     - to_xarray() → 二维 DataArray
     - :doc:`数组格点 <../guide/low-level/grids>`
   * - :py:class:`~nuwe_cmadaas.music.GridScalar2D`
     - to_xarray() → 二维 DataArray
     - :doc:`标量格点 <../guide/low-level/grids>`
   * - :py:class:`~nuwe_cmadaas.music.GridVector2D`
     - to_xarray() → U/V Dataset
     - :doc:`矢量格点 <../guide/low-level/grids>`
   * - :py:class:`~nuwe_cmadaas.music.FilesInfo`
     - files_info 列表；无 pandas/xarray 转换
     - :doc:`清单 <../guide/low-level/file-list>` / :doc:`下载 <../guide/low-level/downloads>`
   * - :py:class:`~nuwe_cmadaas.music.DataBlock`
     - data_name / data bytes；无 pandas/xarray 转换或自动写文件
     - :doc:`数据块 <../guide/low-level/data-block>`

各类构造签名由 autodoc 从实现生成。构造器不会规范化任意调用者提供的数据，
也不会执行服务查询；后面的字段约定主要描述客户端解码后的响应。
不支持的转换继承基类的 NotImplementedError，不承诺所有响应都支持两种转换。
各子类 load_from_protobuf_content(content) 接收序列化 bytes，
load_from_protobuf_object(...) 接收匹配格式的已解析 protobuf 对象；
二者均原地更新响应并返回 None，不能把加载调用的返回值当成响应对象。

请求元数据与共同状态
--------------------

.. currentmodule:: nuwe_cmadaas.music.data

.. autoclass:: RequestInfo
   :members:
   :undoc-members:

.. list-table:: RequestInfo 字段 / 构造参数
   :header-rows: 1

   * - 字段
     - 类型 / 默认
     - 含义
   * - error_code / error_message
     - int=0 / str=""
     - 服务或已处理的本地请求错误；零表示成功状态
   * - request_elements / request_params
     - str=""
     - 服务提供的原始要素/参数描述，不是客户端完整查询字典，也不保证已遮盖认证
   * - request_time / response_time
     - str=""
     - 原始请求/响应时间字符串，不解析成 datetime，不等同于资料时次
   * - row_count / col_count
     - int=0
     - 服务计数；表格解码使用它们，不代表每种响应都具有二维表格结构
   * - take_time
     - int=0
     - 原始服务耗时字段；当前客户端不换算或确认其单位
   * - pb_request_info
     - protobuf RequestInfo 或 None
     - 构造时非 None 则读取其字段，可覆盖上面传入的服务元数据值
   * - cause
     - BaseException 或 None
     - 本地请求处理的可选异常原因；protobuf 不提供该字段

load_protobuf(request_info) 原地复制服务字段并返回 None；不会清除或补充本地 cause。
create_from_protobuf(request_info) 接收已解析 protobuf 对象并返回 RequestInfo，
与 ResponseData 的同名方法接收序列化 bytes 不同。

.. autoclass:: ResponseData
   :members:
   :undoc-members:

构造参数 request=None 会新建 RequestInfo，metadata 初始为独立空字典。
ok 精确判断 request.error_code == 0，不验证非空、单位或内容正确性。
``raise_for_error(*, interface_id=None, params=None)`` 成功返回同一对象；失败按
:doc:`异常分类 <exceptions>` 抛错误，有 cause 时建立异常链。
上下文须显式传入，不从 metadata 推断，也不保存供后续转换使用。

ResponseData.create_from_protobuf(content) 在子类上调用时构造该子类并读取 bytes，
不附加客户端请求 metadata，不自动对业务失败抛异常；直接解码/结构异常会传播。
底层客户端会处理部分解码异常并记录 -10003；直接调用对象加载方法没有该包装。
基类 load_from_protobuf_content/to_pandas/to_xarray 本身均未实现。

metadata 的客户端映射为 interface_id，以及存在时的 time→time、timeRange→time_range、
validTime→valid_time、levelType→level_type、fcstLevel→level、fcstMember→member。
times、dataCode、要素/坐标列表和完整查询不会自动全部保存。转换另补非空的
request_time/response_time，已有同名 metadata 优先；这些 attrs 不创建数据维度。

表格
----

.. currentmodule:: nuwe_cmadaas.music

.. autoclass:: Array2D
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

data 是解码后的二维字符串数组，element_names 为列名 list[str]；row_count/col_count
为表格尺寸，request/metadata 来自共同状态。默认 data=None 使用 (0,0) 空数组，
element_names=None 使用空列表。成功空响应可保留 (0,n) 和列名；非零错误响应
清空 data 与对象计数，request 的原始计数与列名仍按响应保留。
to_pandas() 先检查状态与数据/列数，保留字符串和已有 attrs，不自动处理数值、
单位或缺测。手动构造的 shape 不匹配可以在转换时抛 ValueError。

格点共有字段
------------

三类格点都具有 request/metadata、start_lat/start_lon、end_lat/end_lon、
lat_count/lon_count、lat_step/lon_step 和 lats/lons。
起止、步长默认 0，计数默认 0，坐标 None 使用空列表。data/u_datas/v_datas=None
使用二维空数组；实际成功解码后为 (lat_count,lon_count) 数值数组。

显式非空坐标按原顺序使用并核对长度；否则非零步长用 start+step*index，
步长为零且计数非零时使用起止端点的 linspace。没有排序或插值。
转换维度为 latitude/longitude，坐标单位为 degrees_north/degrees_east。
失败解码响应清空场、坐标和计数；转换先检查状态，随后检查结构。
成功空场与服务失败不同，手动构造对象不保证已经通过 shape/坐标校验。

.. autoclass:: GridArray2D
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

data 对应 RetGridArray2D.data；units/user_element_name 为字符串，默认空值。
to_xarray() 返回二维 DataArray，名称来自 user_element_name，attrs 包含 units
和已有 metadata，没有自动缺测处理、单位换算或额外维度。

.. autoclass:: GridScalar2D
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

data 对应 RetGridScalar2D.datas，其余标量输出行为与数组格点一致。
方法和服务返回格式必须匹配，不能只因二者都能转换 DataArray 就通用替换。

.. autoclass:: GridVector2D
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

u_datas/v_datas 为两个数值场，u_element_name/v_element_name 默认空字符串。
to_xarray() 返回 Dataset，变量名用响应名称，空名称分别回退 u/v；Dataset.attrs
包含 metadata，分量不自动附单位。调用者仍需确认两个要素的名称与单位。

文件信息
--------

.. autoclass:: FileInfo
   :members:
   :undoc-members:

.. list-table:: FileInfo 字段 / 构造参数
   :header-rows: 1

   * - 字段
     - 类型 / 默认
     - 含义
   * - file_name / suffix
     - str=""
     - 服务给出的名称/后缀，不保证文件格式或磁盘存在
   * - save_path / file_url
     - str=""
     - 服务保存路径/下载 URL，save_path 不更新为本地下载路径
   * - size
     - str=""
     - 原始大小描述；不能默认是已校验的数字或实际本地字节数
   * - image_base64
     - str=""
     - 原始图像 base64 字符串，不自动解码
   * - attributes
     - list[str]，None 初始化为空列表
     - 服务属性列表，与响应 metadata 和 pandas/xarray attrs 不同

create_from_protobuf(pb_file_info) 接收已解析 FileInfo protobuf 并返回 FileInfo。
此对象没有 request/ok/raise_for_error；状态在包含它的 FilesInfo 上。

.. autoclass:: FilesInfo
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

files_info 为 FileInfo 列表，None 初始化为空列表；非零服务错误解码后清空列表。
清单查询不写磁盘，downFile/saveAsFile 写文件后仍返回 FilesInfo，不能以清单长度
推断整批已完成。saveAsFile 仅下载第一项，成功空清单现有 IndexError；downFile
允许成功空清单，overwrite 默认 True，批量没有回滚。详见各调用指南和 :doc:`client`。

数据块
------

.. autoclass:: DataBlock
   :members:
   :undoc-members:
   :exclude-members: protobuf_object_type
   :show-inheritance:

构造参数 data_name=None/data=None 分别初始化为 ""/b""；实际解码按 protobuf
dataName/byteArray 返回 str/bytes，非零服务错误也可保留内容。
先检查状态，再检查非空与已知格式；名称不是 Path，没有自动写文件、文本或表格转换。
callAPI_to_dataBlock 每次发出能力 UserWarning，目前没有已验证真实接口/资料组合，
合成或空成功不作为在线支持证据，见 :doc:`数据块指南 <../guide/low-level/data-block>`。
