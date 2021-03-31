# coding=UTF-8
from nuwe_cmadaas import CMADaaSClient
import click
import pathlib


@click.command()
@click.option("--user", help="user name", required=True)
@click.option("--password", help="password name", required=True)
@click.option("--client-config", help="client config file")
def cli(user, password, client_config=None):

    interface_id = "getNafpEleGridByTimeAndLevelAndValidtime"

    server_id = "NAFP_FOR_FTM_KWBC_GLB"

    params = {
        "dataCode": "NAFP_FOR_FTM_KWBC_GLB",
        "time": "20190921000000",
        "fcstEle": "TEM",
        "levelType": "1",
        "fcstLevel": "0",
        "validTime": "0",
    }

    client = CMADaaSClient(
        user=user,
        password=password,
        config_file=client_config)
    result = client.callAPI_to_gridArray2D(
        interface_id, params
    )

    print(result)


if __name__ == "__main__":
    cli()
