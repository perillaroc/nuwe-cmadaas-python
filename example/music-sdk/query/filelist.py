# coding=UTF-8
from cma.music.DataQueryClient import DataQueryClient
import click
import pathlib


@click.command()
@click.option("--user", help="user name", required=True)
@click.option("--password", help="password name", required=True)
@click.option("--client-config", help="client config file")
def cli(user, password, client_config=None):

    interface_id = "getNafpFileByTime"

    server_id = "NMIC_MUSIC_CMADAAS"

    params = {
        "dataCode": "NAFP_FOR_FTM_KWBC_GLB",
        "time": "20190922000000",
    }

    client = DataQueryClient(config_file=client_config)
    result = client.callAPI_to_fileList(
        user, password, interface_id, params
    )

    print(result)


if __name__ == "__main__":
    cli()
