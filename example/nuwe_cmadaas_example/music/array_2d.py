# coding=UTF-8
import click

from nuwe_cmadaas import CMADaaSClient


@click.command()
@click.option("--user", help="user name", required=True)
@click.option("--password", help="password name", required=True)
@click.option("--client-config", help="client config file")
def cli(user, password, client_config=None):

    interface_id = "getSurfEleByTimeRange"

    server_id = "NMIC_MUSIC_CMADAAS"

    params = {
        "dataCode": "SURF_CHN_MUL_HOR",
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,PRS_Sea,TEM,"
        "DPT,WIN_D_INST,WIN_S_INST,PRE_1h,PRE_6h,PRE_24h,PRS",
        "timeRange": "[20210110000000,20210110020000)",
        "orderby": "Station_ID_d:ASC",
        "limitCnt": "10",
    }

    client = CMADaaSClient(
        user=user,
        password=password,
        config_file=client_config)
    result = client.callAPI_to_array2D(interface_id, params, server_id)

    print(result)


if __name__ == "__main__":
    cli()
