**********
站点数据
**********

.. currentmodule:: nuwe_cmadaas.obs

:py:class:`retrieve_obs_station` 函数用于获取地面站点观测数据。


.. code-block:: python

    >>> import pandas as pd
    >>> from nuwe_cmadaas.obs import retrieve_obs_station
    >>> table = retrieve_obs_station(
    ...     "SURF_CHN_MUL_HOR",
    ...     time=[
    ...         pd.to_datetime("2021-01-01 00:00:00"),
    ...         pd.to_datetime("2021-01-02 00:00:00")
    ...     ],
    ...     config_file="cedarkit.yaml"
    ... )
    >>> table
           Station_Id_d      Lat       Lon    Alti  ... PRE_1h  PRE_6h PRE_24h     PRS
    0               631  37.9167  102.6667  1531.5  ...      0       0       0   850.4
    1               631  37.9167  102.6667  1531.5  ...      0       0       0   851.7
    2              7129    44.85      84.7     455  ...      0  999999  999999  999999
    3              7129    44.85      84.7     455  ...      0  999999  999999  999999
    4              9168  46.8472   84.1847     891  ...      0  999999  999999  999999
                 ...      ...       ...     ...  ...    ...     ...     ...     ...
    126047       999999  24.6462  121.0829     718  ...      0       0       0  999998
    126048       999999  23.0817  120.5825     298  ...      0       0       0   986.3
    126049       999999  22.8596  120.5086      44  ...      0       0       0  999998
    126050       999999  24.2965  120.6431     130  ...      0       0       0  999999
    126051       999999  23.0739  120.5289     274  ...      0       0       0  999998
    [126052 rows x 17 columns]




API
===========

.. autofunction:: retrieve_obs_station