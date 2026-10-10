"""Execute migrated examples offline and retain traceability to old scripts."""

import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from examples.__main__ import EXAMPLES, load_legacy_migration, main, render_legacy_index, resolve_legacy
from examples._support.live_config import make_live_music_client
from examples.music import scenarios
from nuwe_cmadaas import model, obs
from nuwe_cmadaas.music import CMADaaSClient


ROOT = Path(__file__).resolve().parents[2]
LEGACY = load_legacy_migration()
pytestmark = pytest.mark.unit


def test_catalog_covers_every_high_level_entry_and_music_method():
    covered = {entry for _, _, entries in EXAMPLES.values() for entry in entries}
    expected = set(model.__all__) | set(obs.__all__) | {
        name for name in vars(CMADaaSClient) if name.startswith("callAPI_to_")
    }
    assert covered == expected


def test_migration_matches_all_original_calls_and_retains_non_date_parameters():
    observed = {}
    for path in (ROOT / "example/nuwe_cmadaas_example").rglob("*.py"):
        tree = ast.parse(path.read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("callAPI_to_")]
        if not calls:
            continue
        values = {n.targets[0].id: n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                  and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
        fmt = values.get("data_format")
        if fmt is None:
            fmt = next((kw.value for kw in calls[0].keywords if kw.arg == "data_format"), None)
        params = {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(values["params"].keys, values["params"].values)
                  if ast.literal_eval(k) not in {"time", "times", "timeRange"}}
        observed[path.relative_to(ROOT / "example/nuwe_cmadaas_example").as_posix()] = {
            "interface_id": ast.literal_eval(values["interface_id"]),
            "method": calls[0].func.attr, "format": ast.literal_eval(fmt) if fmt else None,
            "legacy_parameters": params,
        }
    assert observed.keys() == LEGACY.keys()
    for path, values in observed.items():
        assert all(LEGACY[path][key] == value for key, value in values.items()), path
        record = LEGACY[path]
        interface, method, _, _ = scenarios.SCENARIOS[record["scenario"]]
        assert interface == record["interface_id"]
        if record["operation"] == "query":
            assert method == record["method"]
    assert (ROOT / "example/MIGRATION.md").read_text() == render_legacy_index()


@pytest.mark.parametrize("entry", EXAMPLES)
def test_unified_entry_runs_without_reading_live_config(entry, monkeypatch, capsys):
    def unexpected(*args, **kwargs):
        pytest.fail("An offline example tried to read live configuration")
    monkeypatch.setattr("nuwe_cmadaas.config.load_cmadaas_config", unexpected)
    monkeypatch.setattr("nuwe_cmadaas.music.load_cmadaas_config", unexpected)
    main([entry])
    assert f"{entry}: synthetic contracts passed" in capsys.readouterr().out


@pytest.mark.parametrize("path", LEGACY, ids=LEGACY)
def test_each_legacy_selector_executes_its_actual_method_and_format(path, monkeypatch, capsys):
    clients = []
    original = scenarios.make_synthetic_music_client
    def capture(transport):
        clients.append(transport)
        return original(transport)
    monkeypatch.setattr(scenarios, "make_synthetic_music_client", capture)
    main(["--legacy", path])
    record = LEGACY[path]
    transport, = clients
    method, interface, query_key = transport._parse_api_url(transport.calls[0][0])
    expected_method = "callAPI_to_fileList" if record["operation"] == "download" else record["method"]
    assert method == expected_method and interface == record["interface_id"]
    params = dict(query_key)
    assert params["dataCode"].startswith("SYNTHETIC_")
    if record["format"]:
        assert params["dataFormat"] == record["format"]
    if record["operation"] in {"download", "save"}:
        assert len(transport.responses) == 2 and transport.responses[1].streamed
    else:
        assert len(transport.responses) == 1
    assert all(response.closed for response in transport.responses)
    assert "temporary output removed" in capsys.readouterr().out


def test_unique_native_results_are_actual_tables_grids_and_format_records():
    with redirect_stdout(io.StringIO()):
        statistics = scenarios.run_scenario("station_statistics")
        metadata = scenarios.run_scenario("station_info")
        points = scenarios.run_scenario("model_point")
        vector = scenarios.run_scenario("vector_grid")
        text = scenarios.run_scenario("station_statistics", "serialized", "json")
    assert statistics.loc[0, ["SUM_PRE_1h", "AVG_PRE_1h", "SUM_TEM", "AVG_TEM"]].tolist() == ["6.0", "1.0", "1680.0", "280.0"]
    assert metadata.loc[0, ["Station_ID_C", "Lat", "Lon", "Alti"]].tolist() == ["FAKE001", "39.8", "116.4667", "50.0"]
    assert points[["lat", "validtime"]].values.tolist() == [["39.8", "0"], ["39.8", "12"], ["31.2", "0"], ["31.2", "12"]]
    np.testing.assert_array_equal(vector.WIU.values, [[1, 2, 3], [4, 5, 6]])
    payload = json.loads(text)
    assert payload["returnCode"] == "0" and payload["DS"][0]["AVG_TEM"] == "280.0"


def test_live_params_use_runtime_dates_and_do_not_reuse_synthetic_selectors():
    native = {"dataCode": "AUTHORIZED", "elements": "Verified", "orderby": "Verified:asc", "limitCnt": "10"}
    station = scenarios.make_live_params("station", native, now="2026-10-10 12:30")
    assert station["times"] == "20261009000000" and "times" not in native
    interval = scenarios.make_live_params("station_range", native, now="2026-10-10")
    assert interval["timeRange"] == "[20261009000000,20261009020000)"
    point = scenarios.make_live_params("model_point", {
        "dataCode": "AUTHORIZED_MODEL", "fcstEle": "TEM", "levelType": "100", "fcstLevel": "850",
        "minVT": "0", "maxVT": "12", "latLons": "39.8/116.4667",
    }, now="2026-10-10")
    assert point["time"] == "20261007060000"
    with pytest.raises(ValueError, match="Missing live parameters"):
        scenarios.make_live_params("station", {"dataCode": "AUTHORIZED"})
    for invalid in ({**native, "time": "20260101000000"}, {**native, "dataCode": "SYNTHETIC_CODE"}):
        with pytest.raises(ValueError):
            scenarios.make_live_params("station", invalid)


def test_explicit_live_config_initializes_locally_and_never_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("CEDARKIT_CONFIG", str(tmp_path / "wrong.yaml"))
    with pytest.raises(ValueError, match="explicit"):
        make_live_music_client(None)
    with pytest.raises(FileNotFoundError):
        make_live_music_client(tmp_path / "missing.yaml")
    path = tmp_path / "explicit.yaml"
    path.write_text(yaml.safe_dump({"cmadaas": {
        "auth": {"user": "synthetic-user", "password": "synthetic-password"},
        "server": {"music_server": "synthetic.invalid", "music_port": 80,
                   "music_ServiceId": "synthetic-service", "music_connTimeout": 1, "music_readTimeout": 1},
    }}))
    client = make_live_music_client(path)
    assert client.user == "synthetic-user" and client.server_ip == "synthetic.invalid"
    assert client.log_policy == "summary" and client.max_retries == 0


def test_invalid_selectors_fail_before_constructing_any_client(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid selector constructed a client")
    monkeypatch.setattr(scenarios, "make_synthetic_music_client", unexpected)
    for path in ("../unknown.py", "music/unknown.py"):
        with pytest.raises(SystemExit) as exc:
            main(["--legacy", path])
        assert exc.value.code == 2
    with pytest.raises(ValueError, match="file-list"):
        scenarios.run_scenario("station_statistics", "download")
    with pytest.raises(ValueError, match="only demonstrates"):
        scenarios.run_scenario("vector_grid", "save")
    assert resolve_legacy("example/nuwe_cmadaas_example/music/array_2d.py") == LEGACY["music/array_2d.py"]
