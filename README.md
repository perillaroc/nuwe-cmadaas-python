# nuwe-cmadaas-python

[![Documentation Status](https://readthedocs.org/projects/nuwe-cmadaas-python/badge/?version=latest)](https://nuwe-cmadaas-python.readthedocs.io/zh_CN/latest/?badge=latest)

为 CMADaaS MUSIC 接口封装 Python API，提供仿 MUSIC 原生接口及高层 API 接口，支持 Python 3 和 Windows。

文档：https://nuwe-cmadaas-python.readthedocs.io

## 安装

克隆源码，使用 `pip` 命令安装 nuwe-cmadaas 包。

```
git clone https://github.com/perillaroc/nuwe-cmadaas-python.git
cd nuwe-cmadaas-python
pip install .
```

## 开始使用

MUSIC 接口仅适用于 CMA 内网用户，使用前请先申请账户。

使用 `nuwe_cmadaas.CMADaaSClient` 类从 CMADaaS 中检索数据。

需要提供 MUSIC 服务的相关参数，可以保存在当前目录 `client.conf` 文件中，
或者在创建 `nuwe_cmadaas.CMADaaSClient` 对象显式指定。参数包括：

- `music_server`: MUSIC 接口 ip 地址，必须指定
- `music_port`：MUSIC 接口端口号，必须指定
- `music_connTimeout`：连接超时，秒，可选
- `music_readTimeout`：数据读取超时，秒，可选
- `music_ServiceId`：默认服务节点 id

下面的示例展示如何检索地面观测资料。

```python
from nuwe_cmadaas import CMADaaSClient

client_config_path = "path/to/client.config"
user = "user name"
password = "user password"
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
```

更详细的接口使用方法请访问 CMADaaS 官网。

## 示例

请访问 `example` 目录查看示例。

## License

`nuwe-cmadaas-python` 未做特殊声明部分代码由 Wang Dapeng (CEMC/CMA) 开发，并采用 Apache License 2.0 协议。
