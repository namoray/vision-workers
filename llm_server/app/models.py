from __future__ import annotations


from typing import Any, Optional, Callable
import enum

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    TextIteratorStreamer,
)
from vllm import AsyncLLMEngine
from pydantic import BaseModel, Field


class ToxicEngine(BaseModel):
    model: AutoModelForSeq2SeqLM
    tokenizer: AutoTokenizer

    class Config:
        arbitrary_types_allowed = True


class Role(str, enum.Enum):
    """Message is sent by which role?"""

    user = "user"
    assistant = "assistant"
    system = "system"


class Message(BaseModel):
    role: Role = Role.user
    content: str = "Remind me that I have forgot to set the messages"


class ModelType(str, enum.Enum):
    cortext_lite = "cortext-lite"
    cortext = "cortext"
    cortext_ultra = "cortext-ultra"


# Assuming the necessary import statements for AsyncLLMEngine, schemas.TextRequestModel, TextIteratorStreamer
class RequestInfo(BaseModel):
    messages: list[Message] = Field(
        default_factory=lambda: [
            {
                "role": "user",
                "content": "Remind the user they forgot to give a message, in the style of a 1920s cowboy, in 20 words",
            },
        ],
        description="List of messages where each message has a 'role' and 'content' key.",
    )

    seed: int = Field(
        ..., title="Seed", description="Seed for text generation.", example=0
    )

    temperature: float = Field(
        default=0.5,
        title="Temperature",
        description="Temperature for text generation.",
    )

    max_tokens: int = Field(
        4096, title="Max Tokens", description="Max tokens for text generation."
    )

    number_of_logprobs: int = Field(
        default=1,
        title="Logprobs",
        description="Number of logprobs to return with each token output",
        example=1,
        gt=0,
        le=5,
    )

    starting_assistant_message: bool = Field(
        default=True,
        title="Starting Assistant Message",
        description="Are we starting the assistant message or continuing it? Only needs to be non true for validators",
    )

    top_p: float = Field(
        default=1,
        title="Top P",
        description="Top P for text generation. This nearly always should be 1",
    )

    class Config:
        extra = "allow"


class LLMEngine(BaseModel):
    model_name: str
    tokenizer_name: str
    model: AsyncLLMEngine
    tokenizer: Any
    completion_method: Callable[[LLMEngine, RequestInfo], Any]
    streamer: Optional[TextIteratorStreamer] = None
    processor: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True
