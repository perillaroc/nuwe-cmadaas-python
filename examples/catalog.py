"""Repository example entry points; this module does not initialize clients."""

# name: (module, callable, public API entries demonstrated)
EXAMPLES = {
    "station": ("high_level.station", "run_example", ("retrieve_obs_station",)),
    "obs-grid": ("high_level.grid", "run_example", ("retrieve_obs_grid",)),
    "upper-air": ("high_level.upper_air", "run_example", ("retrieve_obs_upper_air",)),
    "obs-files": ("high_level.files", "run_example", ("download_obs_file",)),
    "upper-air-files": ("high_level.upper_air_files", "run_example", ("download_obs_upper_air_file",)),
    "model-grid": ("high_level.model_grid", "run_example", ("retrieve_model_grid",)),
    "model-point": ("high_level.model_point", "run_example", ("retrieve_model_point",)),
    "model-files": ("high_level.model_files", "run_example", ("download_model_file",)),
    "tables": ("music.tables", "run_example", ("callAPI_to_array2D",)),
    "grids": ("music.grids", "run_example", (
        "callAPI_to_gridArray2D", "callAPI_to_gridScalar2D", "callAPI_to_gridVector2D",
    )),
    "file-list": ("music.files", "run_listing_example", ("callAPI_to_fileList",)),
    "downloads": ("music.files", "run_download_example", ("callAPI_to_downFile",)),
    "serialization": ("music.serialization", "run_serialization_example", ("callAPI_to_serializedStr",)),
    "save-as-file": ("music.serialization", "run_save_example", ("callAPI_to_saveAsFile",)),
    "data-block": ("music.data_block", "run_data_block_example", ("callAPI_to_dataBlock",)),
}
