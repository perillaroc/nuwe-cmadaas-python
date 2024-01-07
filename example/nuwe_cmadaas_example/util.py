from pathlib import Path


def get_output_directory() -> Path:
    output_directory = Path(Path(__file__).parent.parent, "./output")
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def get_client_config_path() -> Path:
    config_file_path = Path(Path(__file__).parent.parent, "./config/client.config")
    if not config_file_path.exists():
        raise FileNotFoundError(f"client.config is not found, create the file in {config_file_path}")
    return config_file_path
