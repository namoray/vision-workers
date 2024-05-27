import enum
from typing import List, Optional

from pydantic import BaseModel


class ChatModels(str, enum.Enum):
    """Model is used for the chat"""

    bittensor_finetune = "bittensor-finetune"
    mixtral = "mixtral-8x7b"
    llama_3 = "llama-3"


class Role(str, enum.Enum):
    """Message is sent by which role?"""

    user = "user"
    assistant = "assistant"
    system = "system"


class Message(BaseModel):
    role: Role = Role.user
    content: str = "Remind me that I have forgot to set the messages"

    class Config:
        extra = "allow"


class EngineEnum(str, enum.Enum):
    DREAMSHAPER = "dreamshaper"
    PLAYGROUND = "playground"
    PROTEUS = "proteus"


class ImageHashes(BaseModel):
    average_hash: str = ""
    perceptual_hash: str = ""
    difference_hash: str = ""
    color_hash: str = ""



class TextPrompt(BaseModel):
    text: str
    weight: Optional[float]

class ImageResponseBody(BaseModel):
    image_b64: Optional[str] = None
    is_nsfw: Optional[bool] = None
    clip_embeddings: Optional[List[float]] = None
    image_hashes: Optional[ImageHashes] = None


class ClipEmbeddingsResponse(BaseModel):
    clip_embeddings: Optional[List[List[float]]] = None

class ClipTextEmbeddingsResponse(BaseModel):
    text_embedding: Optional[List[float]] = None

class SotaResponse(BaseModel):
    image_url: Optional[str]
    error_message: Optional[str]
