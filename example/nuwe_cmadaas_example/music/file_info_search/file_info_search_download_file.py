import click
import pandas as pd
import numpy as np

from nuwe_cmadaas import CMADaaSClient
from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.util import get_time_string

from nuwe_cmadaas_example.util import get_client_config_path, get_output_directory


def query(username: str, password: str, server_id: str, client_config: str):
    interface_id = "getRadaFileByTimeRangeAndStaId"

    yesterday = pd.Timestamp.now().floor(freq="D") - pd.Timedelta(days=1)
    yesterday_01utc = yesterday + pd.Timedelta(hours=1)
    yesterday_time = get_time_string(yesterday)
    yesterday_01utc_time = get_time_string(yesterday_01utc)

    params = {
        "dataCode": "RADA_L2_UFMT",
        "timeRange": f"[{yesterday_time},{yesterday_01utc_time})",
        "staIds": "Z9210,Z9024,Z9010",
    }

    file_dir = get_output_directory()

    client = CMADaaSClient(
        user=username,
        password=password,
        config_file=client_config)
    result = client.callAPI_to_downFile(interface_id, params, file_dir, server_id)

    print("return code:", result.request.error_code)
    print("return message:", result.request.error_message)

    for file_info in result.files_info:
        print(file_info.file_url)


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
