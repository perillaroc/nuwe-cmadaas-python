"""Native legacy scenarios, using synthetic responses by default.

Run ``python -m examples.music.scenarios --help`` from the repository root.
Statistics, station metadata and radar file IDs are preserved as native MUSIC
examples; synthetic execution does not add them to the high-level registry or
prove that a service supports their parameters or requested return formats.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from examples._support import (
    SyntheticTransport, make_array2d_content, make_files_info_content,
    make_grid_array2d_content, make_grid_vector2d_content, make_synthetic_music_client,
)


FORMATS = ("json", "xml", "text", "html")
_GRID_PARAMS = {"fcstEle": "TEM", "levelType": "100", "fcstLevel": "850", "validTime": "24"}
_RECT = {"minLat": "39", "maxLat": "42", "minLon": "115", "maxLon": "117"}
_STATION_PARAMS = {
    "elements": "Station_ID_C,PRE_1h,PRS,RHU,VIS,WIN_S_Avg_2mi,WIN_D_Avg_2mi,Q_PRS",
    "orderby": "Station_ID_d:ASC", "limitCnt": "10",
}
# Each tuple retains the actual old interface, response method and selector shape.
SCENARIOS = {
    "station": ("getSurfEleByTime", "callAPI_to_array2D", "times", _STATION_PARAMS),
    "station_range": ("getSurfEleByTimeRange", "callAPI_to_array2D", "timeRange", {
        "elements": "Station_Id_d,Lat,Lon,Alti,Day,Hour,PRS_Sea,TEM,DPT,WIN_D_INST,WIN_S_INST,PRE_1h,PRE_6h,PRE_24h,PRS",
        "orderby": "Station_ID_d:ASC", "limitCnt": "10",
    }),
    "station_statistics": ("statSurfEle", "callAPI_to_array2D", "timeRange", {
        "elements": "Station_ID_C,Station_Name", "statEles": "SUM_PRE_1h,AVG_PRE_1h,SUM_TEM,AVG_TEM",
        "orderBy": "SUM_PRE_1h:desc", "limitCnt": "10",
    }),
    "station_info": ("getStaInfoInRect", "callAPI_to_array2D", None, {
        "elements": "Station_ID_C,Station_Name,Lat,Lon,Alti", **_RECT,
    }),
    "model_point": ("getNafpEleAtPointByTimeAndLevelAndValidtimeRange", "callAPI_to_array2D", "time", {
        "fcstEle": "TEM", "levelType": "100", "fcstLevel": "850",
        "minVT": "0", "maxVT": "12", "latLons": "39.8/116.4667,31.2/121.4333",
    }),
    "model_grid": ("getNafpEleGridByTimeAndLevelAndValidtime", "callAPI_to_gridArray2D", "time", _GRID_PARAMS),
    "model_grid_surface": ("getNafpEleGridByTimeAndLevelAndValidtime", "callAPI_to_gridArray2D", "time", {
        "fcstEle": "TEM", "levelType": "1", "fcstLevel": "0", "validTime": "0",
    }),
    "model_grid_rect": ("getNafpEleGridInRectByTimeAndLevelAndValidtime", "callAPI_to_gridArray2D", "time", {
        **_GRID_PARAMS, **_RECT,
    }),
    "vector_grid": ("getNafpVectorEleGridByTimeAndLevelAndValidtime", "callAPI_to_gridVector2D", "time", {
        "fcstuele": "WIU", "fcstvele": "WIV", "levelType": "100", "fcstLevel": "850", "validTime": "24",
    }),
    "radar_files": ("getRadaFileByTimeRangeAndStaId", "callAPI_to_fileList", "timeRange", {
        "staIds": "FAKE_RADAR001,FAKE_RADAR002,FAKE_RADAR003",
    }),
    "model_files": ("getNafpFileByTime", "callAPI_to_fileList", "time", {}),
}


def _time_params(name, base):
    selector = SCENARIOS[name][2]
    if selector is None:
        return {}
    start = base.strftime("%Y%m%d%H%M%S")
    if selector == "timeRange":
        hours = 6 if name == "station_statistics" else 2 if name == "station_range" else 1
        end = (base + pd.Timedelta(hours=hours)).strftime("%Y%m%d%H%M%S")
        right = "]" if name == "station_statistics" else ")"
        return {selector: f"[{start},{end}{right}"}
    return {selector: start}


def make_live_params(name, params, *, now=None):
    """Add runtime dates to explicitly supplied, service-confirmed native params.

    No synthetic code, station ID or field list is used as a live fallback.
    Surface queries use yesterday at 00; model queries use three days ago at 06.
    The radar example uses the native MUSIC three-days-ago 06 convention, which
    must be checked against the authorized radar dataset's actual availability.
    Station metadata has no date selector. This function sends no request.
    """
    _, _, selector, defaults = SCENARIOS[name]
    if not isinstance(params, dict):
        raise TypeError("params must be a native parameter dictionary")
    required = {"dataCode", *defaults}
    if required - params.keys():
        raise ValueError(f"Missing live parameters: {sorted(required - params.keys())}")
    if {"time", "times", "timeRange", "dataFormat", "savepath"}.intersection(params):
        raise ValueError("Supply selectors and format separately; dates are calculated at runtime")
    if any(not str(value).strip() or str(value).startswith(("SYNTHETIC_", "FAKE", "EXAMPLE_", "YOUR_"))
           for value in params.values()):
        raise ValueError("Replace all synthetic and placeholder live parameters")
    result = deepcopy(params)
    if selector is not None:
        current = pd.Timestamp.now() if now is None else pd.Timestamp(now)
        surface = name in {"station", "station_range", "station_statistics"}
        base = current.normalize() - pd.Timedelta(days=1 if surface else 3)
        if not surface:
            base += pd.Timedelta(hours=6)
        result.update(_time_params(name, base))
    return result


def _synthetic_params(name):
    return {
        "dataCode": "SYNTHETIC_MIGRATION_" + name.upper(),
        **deepcopy(SCENARIOS[name][3]),
        **_time_params(name, pd.Timestamp("2026-01-02 06:00")),
    }


def _records(name):
    if name == "station_statistics":
        return ["Station_ID_C", "Station_Name", "SUM_PRE_1h", "AVG_PRE_1h", "SUM_TEM", "AVG_TEM"], [
            ["FAKE001", "SyntheticA", "6.0", "1.0", "1680.0", "280.0"],
            ["FAKE002", "SyntheticB", "3.0", "0.5", "1689.0", "281.5"],
        ]
    if name == "station_info":
        return ["Station_ID_C", "Station_Name", "Lat", "Lon", "Alti"], [
            ["FAKE001", "SyntheticA", "39.8", "116.4667", "50.0"],
            ["FAKE002", "SyntheticB", "40.0", "116.0", "60.0"],
        ]
    if name == "model_point":
        return ["lat", "lon", "datetime", "level", "validtime", "TEM_100"], [
            ["39.8", "116.4667", "20260102060000", "850", "0", "280.0"],
            ["39.8", "116.4667", "20260102060000", "850", "12", "281.5"],
            ["31.2", "121.4333", "20260102060000", "850", "0", "282.0"],
            ["31.2", "121.4333", "20260102060000", "850", "12", "283.5"],
        ]
    if name == "station_range":
        return SCENARIOS[name][3]["elements"].split(","), [
            ["FAKE001", "39.8", "116.4667", "50", "2", "6", "1000", "280", "270", "90", "2", "1", "2", "3", "995"],
            ["FAKE002", "40.0", "116.0", "60", "2", "7", "1001", "281.5", "271", "180", "3", "0.5", "1", "2", "996"],
        ]
    if name in {"model_files", "radar_files"}:
        return ["fileName", "size"], [[f"synthetic_{name}.bin", "10"]]
    if name.startswith("model_grid"):
        return ["lat", "lon", "TEM"], [["39.0", "115.0", "280.0"], ["40.0", "116.0", "281.5"]]
    return ["Station_ID_C", "PRE_1h", "PRS", "RHU", "VIS", "WIN_S_Avg_2mi", "WIN_D_Avg_2mi", "Q_PRS"], [
        ["FAKE001", "1.0", "1000.0", "60", "10000", "2.0", "90", "0"],
        ["FAKE002", "0.5", "1001.0", "65", "9000", "3.0", "180", "0"],
    ]


def _formatted(name, fmt):
    columns, rows = _records(name)
    records = [dict(zip(columns, row)) for row in rows]
    if fmt == "json":
        return json.dumps({"returnCode": "0", "DS": records})
    if fmt == "xml":
        root = ET.Element("Response", returnCode="0")
        for record in records:
            ET.SubElement(root, "R", record)
    elif fmt == "html":
        root = ET.Element("table")
        heading = ET.SubElement(ET.SubElement(root, "thead"), "tr")
        for column in columns:
            ET.SubElement(heading, "th").text = column
        body = ET.SubElement(root, "tbody")
        for row in rows:
            tr = ET.SubElement(body, "tr")
            for value in row:
                ET.SubElement(tr, "td").text = value
    elif fmt == "text":
        return 'returnCode="0"\n' + " ".join(columns) + "\n" + "\n".join(" ".join(row) for row in rows) + "\n"
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return ET.tostring(root, encoding="unicode")


def _validate_operation(name, operation, fmt):
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")
    if operation not in {"query", "serialized", "save", "download"} or fmt not in FORMATS:
        raise ValueError("Unsupported operation or format")
    if operation == "download" and SCENARIOS[name][1] != "callAPI_to_fileList":
        raise ValueError("download requires a file-list scenario")
    if name == "vector_grid" and operation != "query":
        raise ValueError("The retained vector scenario only demonstrates gridVector2D")


def query(client, name, params, *, operation="query", fmt="json", output=None):
    """Call the actual public MUSIC method with the selected native query.

    Callers injecting a live client own its lifetime, permissions, bounded query
    and download size checks. The offline CLI never constructs that live client.
    """
    _validate_operation(name, operation, fmt)
    interface, method, _, _ = SCENARIOS[name]
    if operation in {"save", "download"} and output is None:
        raise ValueError("An explicit output path is required")
    if operation == "serialized":
        return client.callAPI_to_serializedStr(interface, params, fmt)
    if operation == "save":
        response = client.callAPI_to_saveAsFile(interface, params, fmt, str(output))
    elif operation == "download":
        response = client.callAPI_to_downFile(interface, params, output, overwrite=False)
    else:
        response = getattr(client, method)(interface, params)
    response.raise_for_error(interface_id=interface, params=params)
    return response


def run_scenario(name, operation="query", fmt="json"):
    """Decode, convert or write synthetic data, assert contracts, then clean up."""
    _validate_operation(name, operation, fmt)
    interface, method, _, _ = SCENARIOS[name]
    params = _synthetic_params(name)
    before = deepcopy(params)
    transport = SyntheticTransport()
    with TemporaryDirectory(prefix="nuwe-native-example-") as directory:
        root = Path(directory)
        output = root / f"result.{fmt}" if operation == "save" else root
        expected_params = deepcopy(params)
        if operation in {"serialized", "save"}:
            expected_params["dataFormat"] = fmt
            method = "callAPI_to_serializedStr" if operation == "serialized" else "callAPI_to_saveAsFile"
        if operation == "save":
            expected_params["savepath"] = str(output)
        if operation == "serialized":
            content = _formatted(name, fmt).encode("utf-8")
        elif operation in {"save", "download"} or method == "callAPI_to_fileList":
            filename = f"synthetic_{name}.bin" if operation != "save" else f"result.{fmt}"
            body = _formatted(name, fmt).encode("utf-8") if operation == "save" else b"FAKE-NATIV"
            url = f"https://synthetic.invalid/migration/{name}/{filename}"
            content = make_files_info_content(file_infos=[{
                "file_name": filename, "size": str(len(body)), "file_url": url,
                "save_path": f"/synthetic/service/{filename}", "attributes": ["synthetic"],
            }])
            if operation in {"save", "download"}:
                transport.register_download(url, body)
            if operation == "download":
                method = "callAPI_to_fileList"
        elif method == "callAPI_to_gridArray2D":
            content = make_grid_array2d_content(
                lats=[39, 40], lons=[115, 116], data=[280, 280.5, 281, 281.5],
                start_lat=39, end_lat=40, start_lon=115, end_lon=116, element_name="TEM",
            )
        elif method == "callAPI_to_gridVector2D":
            content = make_grid_vector2d_content(u_element_name="WIU", v_element_name="WIV")
        else:
            columns, rows = _records(name)
            content = make_array2d_content(element_names=columns, rows=rows)
        transport.register_api(method, interface, expected_params, content)
        client = make_synthetic_music_client(transport)
        response = query(client, name, params, operation=operation, fmt=fmt, output=output)
        if operation == "serialized":
            assert isinstance(response, str) and response == _formatted(name, fmt)
            result = response
        elif operation in {"save", "download"}:
            assert response.ok and len(response.files_info) == 1
            info = response.files_info[0]
            path = output if operation == "save" else root / info.file_name
            assert path.read_bytes() == body and path.stat().st_size == int(info.size)
            assert len(list(root.iterdir())) == 1 and not list(root.rglob("*.part"))
            result = {"name": path.name, "size": path.stat().st_size}
            if operation == "save":
                assert path.read_text() == _formatted(name, fmt)
        elif method == "callAPI_to_array2D":
            result = response.to_pandas()
            columns, rows = _records(name)
            assert result.columns.tolist() == columns and result.values.tolist() == rows
            assert all(isinstance(value, str) for value in result.values.ravel())
        elif method == "callAPI_to_gridArray2D":
            result = response.to_xarray()
            assert result.dims == ("latitude", "longitude") and result.shape == (2, 2)
            assert result.latitude.values.tolist() == [39, 40] and result.longitude.values.tolist() == [115, 116]
            np.testing.assert_allclose(result.values, [[280, 280.5], [281, 281.5]])
        elif method == "callAPI_to_gridVector2D":
            result = response.to_xarray()
            assert set(result.data_vars) == {"WIU", "WIV"}
            np.testing.assert_allclose(result.WIU.values, [[1, 2, 3], [4, 5, 6]])
            np.testing.assert_allclose(result.WIV.values, [[-1, -2, -3], [-4, -5, -6]])
        else:
            info, = response.files_info
            assert info.file_name == f"synthetic_{name}.bin" and info.size == "10"
            result = {"file_name": info.file_name, "size": info.size, "save_path": info.save_path}
        assert params == expected_params
        if operation not in {"save", "serialized"}:
            assert params == before
        if operation not in {"save", "download"}:
            assert list(root.iterdir()) == []
        if operation != "serialized":
            assert response.metadata["interface_id"] == interface
        assert len(transport.calls) == len(transport.responses) == (2 if operation in {"save", "download"} else 1)
        assert sum(r.streamed for r in transport.responses) == int(operation in {"save", "download"})
        assert all(r.closed for r in transport.responses)
    assert not root.exists()
    print(f"Synthetic native scenario: {name}; {interface}; {operation}; {fmt}")
    print(f"Native params: {before}")
    print(result)
    print("Synthetic contracts passed; temporary output removed.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument("--operation", choices=("query", "serialized", "save", "download"), default="query")
    parser.add_argument("--format", choices=FORMATS, default="json")
    args = parser.parse_args(argv)
    try:
        _validate_operation(args.scenario, args.operation, args.format)
    except ValueError as exc:
        parser.error(str(exc))
    run_scenario(args.scenario, args.operation, args.format)


if __name__ == "__main__":
    main()
