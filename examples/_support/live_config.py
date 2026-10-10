"""Explicit live configuration for manually adapted repository examples."""

from pathlib import Path

from nuwe_cmadaas.music import CMADaaSClient, load_cmadaas_config


def make_live_music_client(config_path):
    """Read one explicit CedarKit YAML file; construction sends no request.

    This helper is never used by the default offline CLI. INI connection options
    belong to CMADaaSClient(config_file=...), with user/password supplied separately.
    """
    if config_path is None:
        raise ValueError("An explicit CedarKit YAML path is required")
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    config = load_cmadaas_config(path)
    return CMADaaSClient(config=config, log_policy="summary", max_retries=0)
