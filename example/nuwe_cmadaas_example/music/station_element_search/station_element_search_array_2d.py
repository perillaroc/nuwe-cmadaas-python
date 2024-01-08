import click
import pandas as pd
import numpy as np

from nuwe_cmadaas import CMADaaSClient
from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.util import get_time_string

from nuwe_cmadaas_example.util import get_client_config_path


def query(username: str, password: str, server_id: str, client_config: str):
    interface_id = "getSurfEleByTime"

    yesterday = pd.Timestamp.now().floor(freq="D") - pd.Timedelta(days=1)
    times = get_time_string(yesterday)

    params = {
        "dataCode": "SURF_CHN_MUL_HOR",
        "elements": "Station_ID_C,PRE_1h,PRS,RHU,VIS,WIN_S_Avg_2mi,WIN_D_Avg_2mi,Q_PRS",
        "times": times,
        "orderby": "Station_ID_d:ASC",
        "limitCnt": "10",
    }

    client = CMADaaSClient(
        user=username,
        password=password,
        config_file=client_config)
    result = client.callAPI_to_array2D(interface_id, params, server_id)

    print("return code:", result.request.error_code)
    print("return message:", result.request.error_message)

    print(np.array(result.data))


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
