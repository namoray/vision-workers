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


class TaskConfig(BaseModel):
    server_needed: Optional[ServerType]
    load_model_config: Optional[ModelConfigDetails]
    endpoint: Optional[str]
    checking_function: Callable[
        [QueryResult, Dict[str, Any], TaskConfig],
        Coroutine[Any, Any, Union[float, None]],
    ]

    class Config:
        arbitrary_types_allowed = True


class OrchestratorServerConfig(BaseModel):
    server_needed: ServerType
    load_model_config: dict
    checking_function: str
    task: str
    endpoint: str


class CheckResultsRequest(BaseModel):
    server_config: OrchestratorServerConfig
    result: QueryResult
    payload: dict


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


# TODO: These prob need refactoring - also test models should not be here


class ValidationTest(BaseModel):
    validator_server: ServerInstance
    validator_task: str
    miners_to_test: List[ServerInstance]
    prompts_to_check: List[ChatRequestModel]
    checking_function: Callable[
        [QueryResult, Dict[str, Any], TaskConfig],
        Coroutine[Any, Any, Union[float, None]],
    ]


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
