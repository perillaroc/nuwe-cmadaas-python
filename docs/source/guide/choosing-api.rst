底层兼容 API 与高层 API
=======================

底层兼容调用
------------

适用于需要直接使用任意 MUSIC interface 或保留 MUSIC 原生参数的场景：

.. code-block:: python

   from nuwe_cmadaas.music import CMADaaSClient

   client = CMADaaSClient(config_file="client.config")
   response = client.callAPI_to_array2D(
       "getSurfEleByTime",
       {"dataCode": "SURF_CHN_MUL_HOR", "elements": "Station_Id_C,TEM", "times": "20260102000000"},
   )
   if response.ok:
       table = response.to_pandas()

高层推荐调用
------------

适用于已登记的常用业务组合。高层负责规范化、校验、interface 选择和结果转换：

.. code-block:: python

   import pandas as pd
   from nuwe_cmadaas.obs import retrieve_obs_station

   table = retrieve_obs_station(
       "SURF_CHN_MUL_HOR",
       elements="Station_Id_C,TEM",
       time=pd.Timestamp("2026-01-02"),
       config="/path/to/cedarkit.yaml",
   )

高层入口的默认错误返回保持 ``MusicError``；需要异常控制流时使用
``strict=True``。完整的参数、返回值和支持范围见
:doc:`高层 API 参考 <../reference/high-level>` 与
:doc:`支持矩阵 <../reference/support-matrix>`。

高层 ``config=`` 读取 CedarKit YAML，底层 ``config_file=`` 读取 MUSIC INI。
查找规则与参数优先级分别见 :doc:`高层配置 <configuration/high-level>` 和
:doc:`底层客户端配置 <configuration/music-client>`。
