import enum
from typing import List, Optional
from pydantic import BaseModel


class ChatModels(str, enum.Enum):
    """Model is used for the chat"""

    mixtral = "mixtral-8x7b"
    llama_3 = "llama-3"
    llama_31_8b = "llama-3-1-8b"
    llama_31_70b = "llama-3-1-70b"


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



class TextPrompt(BaseModel):
    text: str
    weight: Optional[float]
    
class ImageHashes(BaseModel):
    average_hash: str = ""
    perceptual_hash: str = ""
    difference_hash: str = ""
    color_hash: str = ""



class ImageResponseBody(BaseModel):
    image_b64: Optional[str] = None
    is_nsfw: Optional[bool] = None
    clip_embeddings: Optional[List[float]] = None
    image_hashes: Optional[ImageHashes] = None

