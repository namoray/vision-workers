from __future__ import annotations
from typing import Dict, List, Optional, Any, Union, Callable, Coroutine
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

AxonScores = Dict[int, float]


class QueryResult(BaseModel):
    formatted_response: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]
    axon_uid: Optional[int]
    response_time: Optional[float]
    error_message: Optional[str]
    failed_axon_uids: List[int] = []


class ChatTokens(BaseModel):
    token: str


class ServerType(Enum):
    LLM = "llm_server"
    IMAGE = "image_server"


class ProdDockerImages(Enum):
    LLM = "corcelio/vision:llm_server-latest"
    IMAGE = "corcelio/vision:image_server-latest"


class Tasks(Enum):
    chat_mixtral = "chat-mixtral"
    chat_mixtral4b = "chat-mixtral4b"
    chat_llama_3 = "chat-llama-3"
    chat_llama_31_8b = "chat-llama-31-8b"
    chat_llama_31_70b = "chat-llama-31-70b"
    proteus_text_to_image = "proteus-text-to-image"
    playground_text_to_image = "playground-text-to-image"
    dreamshaper_text_to_image = "dreamshaper-text-to-image"
    proteus_image_to_image = "proteus-image-to-image"
    playground_image_to_image = "playground-image-to-image"
    dreamshaper_image_to_image = "dreamshaper-image-to-image"
    avatar = "avatar"
    upscale = "upscale"
    jugger_inpainting = "inpaint"
    jugger_outpainting = "outpaint"
    clip_image_embeddings = "clip-image-embeddings"
    sota = "sota"


class ModelConfigDetails(BaseModel):
    model: str
    tokenizer: Optional[str] = None
    half_precision: Optional[bool] = None
    revision: Optional[str] = None
    gpu_memory_utilization : Optional[float] = 0.8
    max_model_len : Optional[int] = None



class TaskConfig(BaseModel):
    server_needed: Optional[ServerType]
    load_model_config: Optional[ModelConfigDetails]
    endpoint: Optional[str]
    checking_function: Callable[
        [QueryResult, Dict[str, Any], TaskConfig],
        Coroutine[Any, Any, Union[float, None]],
    ]
    synthetic_generation_function: Optional[Callable] = None
    synthetic_generation_params: Optional[Dict[str, Any]] = None
    task: Tasks

    class Config:
        arbitrary_types_allowed = True


class TaskConfigMapping(BaseModel):
    tasks: Dict[Tasks, TaskConfig]


class TestInstanceResults(BaseModel):
    task: Tasks
    score: float
    miner_server: ServerInstance
    validator_server: ServerInstance
    messages: List[Message]
    temperature: float
    seed: int
    miner_request: Any



class CheckResultsRequest(BaseModel):
    task: Tasks
    synthetic_query: bool
    result: QueryResult
    synapse: Dict[str, Any]

    def dict(self, *args, **kwargs):
        obj_dict = super().dict(*args, **kwargs)
        # Converting Enum instance to its value
        obj_dict["task"] = obj_dict["task"].value
        return obj_dict


class Message(BaseModel):
    role: str
    content: str


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


class ValidationTest(BaseModel):
    validator_server: ServerInstance
    validator_task: Tasks
    miners_to_test: List[ServerInstance]
    prompts_to_check: List[ChatRequestModel]
    checking_function: Callable[
        [QueryResult, Dict[str, Any], TaskConfig],
        Coroutine[Any, Any, Union[float, None]],
    ]


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


class SyntheticGenerationRequest(BaseModel):
    task: Tasks


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
    axon_scores: Optional[AxonScores] = None
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