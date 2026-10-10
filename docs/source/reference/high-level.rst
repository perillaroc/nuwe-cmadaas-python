高层 API 参考
=============

高层 API 只覆盖已经登记、具有稳定参数组合和返回契约的常用场景。函数接受
``pandas``、标准库 ``datetime`` 和普通 Python 容器；未覆盖的 MUSIC 能力请使用
``nuwe_cmadaas.music.CMADaaSClient``。

八个入口均由根包重导出，并在 obs/model 命名空间提供稳定入口。
签名和参数下文从实现生成；参数组合按各指南的登记边界使用，不能将全部可选
参数任意组合，内部 feature 名也不是公开参数名。

.. list-table:: 入口、成功返回与指南
   :header-rows: 1

   * - 入口
     - 成功返回
     - 指南
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_station`
     - DataFrame（latest 返回 Datetime 表）
     - :doc:`地面站点 <../guide/high-level/obs/station>`
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_grid`
     - 二维 DataArray
     - :doc:`地面格点 <../guide/high-level/obs/grid>`
   * - :py:func:`~nuwe_cmadaas.obs.retrieve_obs_upper_air`
     - DataFrame（latest 结构不同）
     - :doc:`高空观测 <../guide/high-level/obs/upper-air>`
   * - :py:func:`~nuwe_cmadaas.obs.download_obs_file`
     - list[Path]
     - :doc:`地面文件 <../guide/high-level/obs/files>`
   * - :py:func:`~nuwe_cmadaas.obs.download_obs_upper_air_file`
     - list[Path]
     - :doc:`高空文件 <../guide/high-level/obs/upper-air-files>`
   * - :py:func:`~nuwe_cmadaas.model.retrieve_model_grid`
     - 二维 DataArray
     - :doc:`模式格点 <../guide/high-level/model/grid>`
   * - :py:func:`~nuwe_cmadaas.model.retrieve_model_point`
     - DataFrame
     - :doc:`模式点 <../guide/high-level/model/point>`
   * - :py:func:`~nuwe_cmadaas.model.download_model_file`
     - list[Path]；latest 查询不是文件下载
     - :doc:`模式文件 <../guide/high-level/model/files>`

共同契约
--------

config 是内层 CedarKit 配置字典或 YAML 路径；client 非 None 时忽略 config，
不读配置文件，见 :doc:`configuration`。strict=False 的失败响应返回
:py:class:`~nuwe_cmadaas.music.MusicError` 并发出兼容弃用警告；strict=True 抛
:py:exc:`~nuwe_cmadaas.music.CMADaaSError` 子类，具体见 :doc:`exceptions`。
参数、配置与本地转换异常仍可直接抛出；strict 不保证所有异常均结构化。

成功表格保留原始字符串；单位、缺测和数值化由调用者按资料定义处理。
格点的 attrs 是描述，不自动创建时间/层次/成员维度。成功空表/空场/[]
与失败不同，见 :doc:`responses` 和 :doc:`结果指南 <../guide/results>`。
下载有实际文件副作用，默认覆盖且批量不回滚；高层没有本地 overwrite 开关，
需要禁止覆盖时用底层 downFile。服务能力和权限须独立确认，登记不等于在线成功。

模式
----

.. currentmodule:: nuwe_cmadaas.model

.. autofunction:: retrieve_model_grid
.. autofunction:: retrieve_model_point
.. autofunction:: download_model_file

观测
----

.. currentmodule:: nuwe_cmadaas.obs

.. autofunction:: retrieve_obs_station
.. autofunction:: retrieve_obs_grid
.. autofunction:: retrieve_obs_upper_air
.. autofunction:: download_obs_file
.. autofunction:: download_obs_upper_air_file

底层客户端另见 :doc:`客户端参考 <client>`。
