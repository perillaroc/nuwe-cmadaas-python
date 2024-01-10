from pathlib import Path

import click
import pandas as pd
import numpy as np

from nuwe_cmadaas import CMADaaSClient
from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.util import get_time_string

from nuwe_cmadaas_example.util import get_client_config_path, get_output_directory


def query(username: str, password: str, server_id: str, client_config: str):
    interface_id = "getNafpEleAtPointByTimeAndLevelAndValidtimeRange"

    yesterday = pd.Timestamp.now().floor(freq="D") - pd.Timedelta(days=1)
    yesterday_time = get_time_string(yesterday)

    params = {
        'dataCode': "NAFP_ANA_FTM_GRAPES_GFS_NEHE",
        'time': yesterday_time,
        'minVT': "0",
        'maxVT': "12",
        'latLons': "39.8/116.4667,31.2/121.4333",
        'fcstEle': "TEM",
        'levelType': "100",
        'fcstLevel': "850",
    }

    data_format = "html"

    client = CMADaaSClient(
        user=username,
        password=password,
        config_file=client_config)
    result = client.callAPI_to_serializedStr(interface_id, params, data_format, server_id)

    print(result)


@click.command()
@click.option("--user", help="user name")
@click.option("--password", help="password name")
@click.option("--server-id", help="server id")
@click.option("--client-config", help="client config file path")
def cli(user=None, password=None, server_id=None, client_config=None):
    if user is None or password is None:
        config = load_cmadaas_config()
        if user is None:
            user = config["auth"]["user"]
        if password is None:
            password = config["auth"]["password"]
        if server_id is None:
            server_id = config["server"]["music_ServiceId"]

    if client_config is None:
        client_config = get_client_config_path()

    query(username=user, password=password, server_id=server_id, client_config=client_config)


if __name__ == "__main__":
    cli()
