from typing import List
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    version: str = "1.0.0"
    environment: str = "prod"
    debug: bool = "False"
    cors_origins: List[str] = ["*"]
