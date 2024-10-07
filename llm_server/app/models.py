from __future__ import annotations
from typing import Any, Optional, Callable, List, Union, Literal
import enum

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TextIteratorStreamer
from vllm import AsyncLLMEngine
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    RootModel,
    ValidationError,
)


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


class TextContent(BaseModel):
    c_type: Literal["text"] = Field("text", alias="type")
    text: str = Field(...)


class ImageContent(BaseModel):
    c_type: Literal["image_url"] = Field("image_url", alias="type")
    url: str = Field(...)


class Content(RootModel[Union[TextContent, ImageContent]]):
    pass


class Message(BaseModel):
    role: Role
    content: Union[str, List[Content]] = Field(...)

    @field_validator("content")
    def check_content_length(cls, value):
        if isinstance(value, list) and len(value) > 2:
            raise ValidationError("The content list cannot contain more than 2 items.")
        return value

    class Config:
        use_enum_values = True


# Vllm support communication following this rules (OpenAI compatible)
# Using openai chat completion
#
# response = client.chat.completions.create(
#     messages=[{
#         "role":
#         "user",
#         "content": [
#             {
#                 "type": "text",
#                 "text": "What's in this image?"
#             },
#             {
#                 "type": "image_url",
#                 "image_url": {
#                     # Can be any of base64 image or http(s) url
#                     # "url": f"data:image/jpeg;base64,{image_base64}" base64 image
#                     "url": f"https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
#                 },
#             },
#         ],
#     }],
#     model=model,
#     max_tokens=64,
# )
#
# # The simplest way with no images
# response = client.chat.completions.create(
#     messages=[{
#         "role": "user",
#         "content": "Simple text message"
#     }],


class MessageResponse(BaseModel):
    role: Role
    content: str
    logprob: float


class ModelType(str, enum.Enum):
    cortext_lite = "cortext-lite"
    cortext = "cortext"
    cortext_ultra = "cortext-ultra"


class RequestInfo(BaseModel):
    messages: List[Message] = Field(
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
