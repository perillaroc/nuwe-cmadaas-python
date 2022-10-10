********
开始使用
********

MUSIC 接口仅适用于 CMA 内网用户，使用前请先申请账户。

使用 :py:class:`nuwe_cmadaas.CMADaaSClient` 类从 CMADaaS 中检索数据。

需要提供 CMADaaS 服务的相关参数，可以保存在当前目录 ``client.conf`` 文件中，
或者在创建 :py:class:`nuwe_cmadaas.CMADaasClient` 对象显式指定。参数包括：

- ``music_server``: MUSIC接口ip地址，必须指定
- ``music_port``：MUSIC接口端口号，必须指定
- ``music_connTimeout``：连接超时，秒，可选
- ``music_readTimeout``：数据读取超时，秒，可选
- ``music_ServiceId``：默认服务节点id

下面的示例展示如何检索地面观测资料。

.. code-block:: python

    from nuwe_cmadaas import CMADaaSClient

    client_config_path="path/to/client/config/file"
    user="user name"
    password="user password"
    server_id = "server id"

    interface_id = "getSurfEleByTimeRange"

    params = {
        "dataCode": "SURF_CHN_MUL_HOR",
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,PRS_Sea,TEM,DPT,WIN_D_INST,WIN_S_INST,PRE_1h,PRE_6h,PRE_24h,PRS",
        "timeRange": "[20190817000000,20190817020000)",
        "orderby": "Station_ID_d:ASC",
        "limitCnt": "10",
    }

    client = CMADaaSClient(
        user=user,
        password=password,
        config_file=client_config_path
    )
    result = client.callAPI_to_array2D(interface_id, params)

更详细的接口使用方法请访问 CMADaaS 官网。