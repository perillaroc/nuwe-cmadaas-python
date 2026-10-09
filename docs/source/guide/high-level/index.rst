高层接口
========

高层函数按资料类别选择已登记的 MUSIC interface，并将成功响应转换为表格、二维格点
或下载文件路径。与底层的同任务调用对照见 :doc:`接口选择 <../choosing-api>`。

客户端选择、YAML 查找规则与 ``client=`` 优先级见
:doc:`高层配置 <../configuration/high-level>`。

按业务选择入口
--------------

.. list-table::
   :header-rows: 1

   * - 资料
     - 公开入口
     - 成功返回值
   * - 地面站点
     - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_station`
     - ``pandas.DataFrame``
   * - 地面格点
     - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_grid`
     - ``xarray.DataArray``
   * - 高空观测
     - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_upper_air`
     - ``pandas.DataFrame``
   * - 地面文件
     - :py:func:`~nuwe_cmadaas.obs.download_obs_file`
     - ``list[Path]``
   * - 高空文件
     - :py:func:`~nuwe_cmadaas.obs.download_obs_upper_air_file`
     - ``list[Path]``
   * - 模式预报／分析格点
     - :py:func:`~nuwe_cmadaas.model.retrieve_model_grid`
     - ``xarray.DataArray``
   * - 模式点／站点预报
     - :py:func:`~nuwe_cmadaas.model.retrieve_model_point`
     - ``pandas.DataFrame``
   * - 模式文件
     - :py:func:`~nuwe_cmadaas.model.download_model_file`
     - ``list[Path]``

查询条件按 :doc:`观测数据 <obs/index>` 与 :doc:`模式数据 <model/index>` 分开介绍。

通用参数与边界
--------------

.. list-table::
   :header-rows: 1

   * - 参数
     - 使用方式
   * - ``data_code``
     - 资料代码；接口、要素、层次和资料权限必须相互匹配。
   * - ``elements`` / ``parameter``
     - 表格类观测使用 ``elements``；格点和模式类使用 ``parameter``。以各函数签名为准。
   * - ``time`` / ``start_time`` / ``forecast_time``
     - 观测时间、模式起报时间、预报时效分别使用不同参数；支持的类型与组合由具体入口决定。
   * - ``station`` / ``point`` / ``region`` / ``level_type`` / ``level``
     - 按资料与入口设置空间、站点和层次条件；不能假定每个函数都支持这些参数。
   * - ``config`` / ``client``
     - YAML 路径或配置字典；显式 ``client=`` 优先，忽略 ``config=``。
   * - ``strict``
     - 默认 ``False`` 返回 ``MusicError``；设为 ``True`` 时服务错误抛出 ``CMADaaSError``。
   * - ``output_dir``
     - 下载函数的输出目录；返回路径对应实际下载文件。空清单成功时返回 ``[]``。

高层只接受已登记的业务组合，未支持组合在请求前抛出 ``UnsupportedQueryError``。
注册表内部的 ``time_range``、``valid_time`` 等 feature 名不是公开函数参数；
请从 :doc:`高层 API 参考 <../../reference/high-level>` 查看完整签名。
资料的真实服务能力还需要对应的权限、时次和接口支持，不能仅凭函数参数或登记推断。

使用返回结果
------------

表格保留原始字段名和字符串值；计算前自行按资料定义进行数值化、缺测处理和单位转换。
格点使用 ``latitude/longitude`` 维度，单位随资料返回；当前高层入口不提供风矢量
``Dataset``，需要该响应形式时使用 :doc:`底层接口 <../low-level/index>`。
结果的 ``attrs`` 包含已有请求元数据，不能将它们当作额外的时间或集合维度。

服务报错与合法空结果不同；默认模式下应先判断是否得到 ``MusicError``，再操作表格、
格点或路径。参数、配置及本地文件操作也可能产生异常，``strict=False`` 不会隐藏
全部本地错误。

可执行通用示例见 :doc:`使用返回结果 <../results>` 和 :doc:`错误处理 <../errors>`。

.. toctree::
   :maxdepth: 2

   obs/index
   model/index
