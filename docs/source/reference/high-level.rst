高层 API 参考
=============

高层 API 只覆盖已经登记、具有稳定参数组合和返回契约的常用场景。函数接受
``pandas``、标准库 ``datetime`` 和普通 Python 容器；未覆盖的 MUSIC 能力请使用
``nuwe_cmadaas.music.CMADaaSClient``。

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
