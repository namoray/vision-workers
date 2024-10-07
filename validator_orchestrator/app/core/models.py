from __future__ import annotations
from typing import Dict, List, Optional, Any, Union, Callable, Coroutine, Literal, Union
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    RootModel,
    ValidationError,
)
from datetime import datetime

AxonScores = Dict[int, float]


class QueryResult(BaseModel):
    formatted_response: dict[str, Any] | list[dict[str, Any]] | None
    node_id: Optional[int]
    response_time: Optional[float]


class ChatTokens(BaseModel):
    token: str


class ServerType(Enum):
    LLM = "llm_server"
    IMAGE = "image_server"


class ProdDockerImages(Enum):
    LLM = "corcelio/vision:llm_server-latest"
    IMAGE = "corcelio/vision:image_server-latest"


class ModelConfigDetails(BaseModel):
    model: str
    tokenizer: Optional[str] = None
    half_precision: Optional[bool] = None
    revision: Optional[str] = None
    gpu_memory_utilization: Optional[float] = 0.8
    max_model_len: Optional[int] = None


class OrchestratorServerConfig(BaseModel):
    server_needed: ServerType = Field(examples=[ServerType.LLM, ServerType.IMAGE])
    load_model_config: dict | None = Field(
        examples=[
            {
                "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
                "half_precision": True,
                "tokenizer": "tau-vision/llama-tokenizer-fix",
                "max_model_len": 16000,
                "gpu_utilization": 0.6,
            },
            None,
        ]
    )
    checking_function: str = Field(examples=["check_text_result", "check_image_result"])
    task: str = Field(examples=["chat-llama-3-1-8b"])
    endpoint: str = Field(examples=["/generate_text"])


class CheckResultsRequest(BaseModel):
    server_config: OrchestratorServerConfig
    result: QueryResult
    payload: dict


class TextContent(BaseModel):
    c_type: Literal["text"] = Field("text", alias="type")
    text: str = Field(...)


class ImageContent(BaseModel):
    c_type: Literal["image_url"] = Field("image_url", alias="type")
    url: str = Field(...)


class Content(RootModel[Union[TextContent, ImageContent]]):
    pass


class Message(BaseModel):
    role: str
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
    role: str
    content: str
    logprob: float


class ChatRequestModel(BaseModel):
    messages: list[Message]
    seed: int
    temperature: float
    max_tokens: int
    top_k: int
    number_of_logprobs: int
    starting_assistant_message: bool


class MinerChatResponse(BaseModel):
    text: str
    logprob: float


# TODO: These prob need refactoring - also test models should not be here


# class ValidationTest(BaseModel):
#     validator_server: ServerInstance
#     validator_task: str
#     miners_to_test: List[ServerInstance]
#     prompts_to_check: List[ChatRequestModel]
#     checking_function: Callable[
#         [QueryResult, Dict[str, Any], TaskConfig],
#         Coroutine[Any, Any, Union[float, None]],
#     ]


class TestInstanceResults(BaseModel):
    task: str
    score: float
    miner_server: ServerInstance
    validator_server: ServerInstance
    messages: List[Message]
    temperature: float
    seed: int
    miner_request: Any


class ServerDetails(BaseModel):
    id: str
    cuda_version: str
    gpu: str
    endpoint: str


class ServerInstance(BaseModel):
    server_details: ServerDetails
    model: Optional[ModelConfigDetails]


class Logprob(BaseModel):
    index: int
    logprob: float
    decoded: str


class ValidatorCheckingResponse(BaseModel):
    text: str
    logprobs: List[Logprob]


class CheckResultResponse(BaseModel):
    task_id: Union[str, None]
    status: TaskStatus


class TaskResultResponse(BaseModel):
    task_id: str
    result: Union[Dict, str]


class CheckTaskResponse(BaseModel):
    task_id: str
    result: Optional[TaskResult] = None
    status: TaskStatus


class TaskResult(BaseModel):
    node_scores: Optional[AxonScores] = None
    timestamp: datetime
    error_message: Optional[str] = None
    traceback: Optional[str] = None


class TaskStatus(Enum):
    Processing = "Processing"
    Success = "Success"
    Failed = "Failed"
    Busy = "Busy"
    Missing = "Missing"


class AllTaskStatusResponse(BaseModel):
    tasks: Dict[str, TaskStatus]
