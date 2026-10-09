"""Offline contracts for the configuration sources described in the guides."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from nuwe_cmadaas.config import load_cmadaas_config
from nuwe_cmadaas.music import CMADaaSClient, create_client
from nuwe_cmadaas.obs import retrieve_obs_station
from tests.fixtures import FakeCMADaaSClient, make_array2d_response


pytestmark = pytest.mark.unit


@pytest.fixture
def config_object():
    return {
        "auth": {"user": "dictionary-user", "password": "dictionary-password"},
        "server": {
            "music_server": "dictionary.invalid",
            "music_port": 8000,
            "music_ServiceId": 7,
            "music_connTimeout": 10,
            "music_readTimeout": 60,
        },
    }


@pytest.fixture
def ini_file(tmp_path):
    path = tmp_path / "client.config"
    path.write_text(
        "[Pb]\n"
        "music_server = ini.invalid\n"
        "music_port = 8001\n"
        "music_ServiceId = 8\n"
        "music_connTimeout = 11\n"
        "music_readTimeout = 61\n"
        "user = ignored-ini-user\n"
        "password = ignored-ini-password\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("source", ["explicit-string", "explicit-path", "environment", "default"])
def test_yaml_lookup_uses_one_source_without_merging(
    source, tmp_path, monkeypatch, config_object
):
    home = tmp_path / "home"
    default = home / ".config" / "cedarkit.yaml"
    default.parent.mkdir(parents=True)
    paths = {
        "explicit": tmp_path / "explicit.yaml",
        "environment": tmp_path / "environment.yaml",
        "default": default,
    }
    for name, path in paths.items():
        value = {
            "auth": {"user": name, "password": f"{name}-password"},
            "server": config_object["server"],
        }
        path.write_text(yaml.safe_dump({"cmadaas": value}), encoding="utf-8")

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("CEDARKIT_CONFIG", str(paths["environment"]))
    argument = None
    if source.startswith("explicit"):
        argument = paths["explicit"]
        if source == "explicit-string":
            argument = str(argument)
        expected_user = "explicit"
    else:
        expected_user = source
        if source == "default":
            monkeypatch.delenv("CEDARKIT_CONFIG")

    loaded = load_cmadaas_config(argument)
    assert "cmadaas" not in loaded
    assert loaded["auth"]["user"] == expected_user
    client = create_client(argument)
    assert client.user == expected_user
    assert client.password == f"{expected_user}-password"
    assert client.server_ip == "dictionary.invalid"
    assert client._connection.timeout == (10, 60)


def test_config_object_bypasses_yaml_lookup(tmp_path, monkeypatch, config_object):
    monkeypatch.setenv("CEDARKIT_CONFIG", str(tmp_path / "missing.yaml"))
    client = create_client(config_object)
    assert client.user == "dictionary-user"
    assert client.server_port == 8000


def test_explicit_missing_yaml_does_not_fall_back(tmp_path, monkeypatch, config_object):
    environment = tmp_path / "environment.yaml"
    environment.write_text(yaml.safe_dump({"cmadaas": config_object}), encoding="utf-8")
    monkeypatch.setenv("CEDARKIT_CONFIG", str(environment))
    with pytest.raises(FileNotFoundError):
        create_client(tmp_path / "missing.yaml")


def test_high_level_client_bypasses_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("CEDARKIT_CONFIG", str(tmp_path / "missing-environment.yaml"))
    client = FakeCMADaaSClient(make_array2d_response())
    table = retrieve_obs_station(
        "SYNTHETIC_STATION",
        elements="Station_Id_C,Lat,Lon,TEM",
        time=pd.Timestamp("2026-01-02"),
        config=tmp_path / "missing-explicit.yaml",
        client=client,
        strict=True,
    )
    assert table["Station_Id_C"].tolist() == ["FAKE001", "FAKE002"]
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({}, ("ini.invalid", 8001, "8", 11, 61, "dictionary-user")),
        (
            {"server_port": 8080, "connection_timeout": 5, "user": "explicit-user"},
            ("ini.invalid", 8080, "8", 5, 61, "explicit-user"),
        ),
        (
            {
                "server_ip": "",
                "server_port": 0,
                "server_id": "",
                "connection_timeout": 0,
                "user": "",
            },
            ("", 0, "", 0, 61, ""),
        ),
    ],
)
def test_ini_precedes_dictionary_but_preserves_explicit_values(
    overrides, expected, ini_file, config_object
):
    client = CMADaaSClient(config_file=ini_file, config=config_object, **overrides)
    assert (
        client.server_ip,
        client.server_port,
        client.server_id,
        client.connect_timeout,
        client.read_timeout,
        client.user,
    ) == expected
    assert client.password == "dictionary-password"
    assert client._connection.timeout == expected[3:5]


def test_low_level_constructor_does_not_discover_files(ini_file, monkeypatch):
    monkeypatch.chdir(ini_file.parent)
    # Neither the existing default INI nor the YAML environment variable is read.
    monkeypatch.setenv("CEDARKIT_CONFIG", str(ini_file))
    client = CMADaaSClient()
    assert client.server_ip is None
    assert client.server_port is None
    assert client.server_id is None
    assert client.user is None
    assert client.password is None
    assert client._connection.timeout == (None, None)


def test_missing_ini_does_not_fall_back_to_dictionary(tmp_path, config_object):
    with pytest.raises(RuntimeError, match="config file is not exist"):
        CMADaaSClient(config_file=tmp_path / "missing.config", config=config_object)


def test_per_request_service_node_does_not_change_default(config_object):
    client = CMADaaSClient(config=config_object)
    url = client._get_fetch_url("syntheticInterface", "callAPI_to_array2D", {}, "override")
    assert "serviceNodeId=override&" in url
    assert client.server_id == 7


def test_create_connect_updates_auth_and_reuses_connection_settings(config_object):
    client = CMADaaSClient(config=config_object, max_retries=1)
    previous = client._connection
    client.create_connect("replacement-user", "replacement-password")
    assert client.user == "replacement-user"
    assert client.password == "replacement-password"
    assert client._connection is not previous
    assert client._connection.timeout == (10, 60)
    assert client._connection.max_retries == 1
