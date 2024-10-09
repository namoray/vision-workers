from pydantic_settings import BaseSettings
from enum import Enum


class Settings(BaseSettings):
    version: str = "1.0.0"
    environment: str = "prod"
    debug: bool = False
    cors_origins: list[str] = ["*"]


class Endpoints(Enum):
    text_to_image = "/text-to-image"
    text_to_image_dynamic = "/text-to-image-dynamic"
    image_to_image = "/image-to-image"
    avatar = "/avatar"
    inpaint = "/inpaint"
    upscale = "/upscale"
    clip_embeddings = "/clip-embeddings"


settings = Settings()
