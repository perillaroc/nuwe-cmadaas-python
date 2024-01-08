from pathlib import Path

import click
import pandas as pd
import numpy as np

from nuwe_cmadaas import CMADaaSClient
from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.util import get_time_string

from nuwe_cmadaas_example.util import get_client_config_path, get_output_directory


def query(username: str, password: str, server_id: str, client_config: str):
    interface_id = "getStaInfoInRect"

    params = {
        "dataCode": "STA_INFO_SURF_CHN",
        "elements": "Station_ID_C,Station_Name,Lat,Lon,Alti",
        "minLat": "39",
        "maxLat": "42",
        "minLon": "115",
        "maxLon": "117"
    }

    data_format = "text"

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
