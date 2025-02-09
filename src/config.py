import json
from typing import Dict

from pydantic import BaseModel

class Configuration(BaseModel):
    """
    Configuration class that loads and stores settings from a JSON config file.

    Attributes:
        models (Dict): Configuration settings for models
        splitter (Dict): Configuration settings for text splitter
        vector_store (Dict): Configuration settings for vector store
        database (Dict): Configuration settings for database

    Args:
        path_to_config (str): Path to JSON configuration file
    """
    models: Dict
    splitter: Dict
    vector_store: Dict
    database: Dict

    def __init__(self, path_to_config: str):
        with open(path_to_config, encoding="utf-8", mode="r") as f:
            data = json.load(f)
        super().__init__(**data)