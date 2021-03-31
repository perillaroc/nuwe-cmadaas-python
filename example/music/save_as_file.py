# coding=UTF-8
from nuwe_cmadaas import CMADaaSClient
import click


@click.command()
@click.option("--user", help="user name", required=True)
@click.option("--password", help="password name", required=True)
@click.option("--client-config", help="client config file")
@click.option("--output-file", help="client config file", required=True)
def cli(user, password, output_file, client_config=None):

    interface_id = "getSurfEleByTimeRange"

    server_id = "NMIC_MUSIC_CMADAAS"

    params = {
        "dataCode": "SURF_CHN_MUL_HOR",
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,PRS_Sea,TEM,"
        "DPT,WIN_D_INST,WIN_S_INST,PRE_1h,PRE_6h,PRE_24h,PRS",
        "timeRange": "[20190817000000,20190817020000)",
        "orderby": "Station_ID_d:ASC",
        "limitCnt": "10",
    }

    client = CMADaaSClient(
        user=user,
        password=password,
        config_file=client_config
    )
    result = client.callAPI_to_saveAsFile(
        interface_id,
        params,
        data_format="json",
        file_name=output_file
    )

    print(result)


if __name__ == "__main__":
    cli()
