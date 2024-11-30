import json
import os
from pydantic import BaseModel, Field
from typing import Dict, Any, Callable, Literal, Optional, Union, List


class ChatMessage(BaseModel):
    role: str
    content: str


class Logprob(BaseModel):
    logprob: float
    rank: Optional[int] = None
    decoded_token: Optional[str] = None


class ResponseFormat(BaseModel):
    type: Literal["text", "json_object", "json_schema"]
    json_schema: Optional[Dict] = None


class BaseRequest(BaseModel):
    model: str
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = 0
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    response_format: Optional[ResponseFormat] = None
    seed: Optional[int] = Field(None, ge=0, le=9223372036854775807)
    stop: Optional[Union[str, List[str]]] = Field(default_factory=list)
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    best_of: Optional[int] = None
    use_beam_search: bool = False
    top_k: int = -1
    min_p: float = 0.0
    repetition_penalty: float = 1.0
    length_penalty: float = 1.0
    stop_token_ids: Optional[List[int]] = Field(default_factory=list)
    include_stop_str_in_output: bool = False
    ignore_eos: bool = False
    min_tokens: int = 0
    skip_special_tokens: bool = True
    spaces_between_special_tokens: bool = True
    prompt_logprobs: Optional[int] = None


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0
    completion_tokens: Optional[int] = 0


class ChatCompletionRequest(BaseRequest):
    messages: List[ChatMessage]


class CompletionRequest(BaseRequest):
    prompt: str


class ChatCompletionLogProb(BaseModel):
    token: str
    logprob: float = -9999.0
    bytes: Optional[List[int]] = None


class ChatCompletionLogProbsContent(ChatCompletionLogProb):
    top_logprobs: List[ChatCompletionLogProb] = Field(default_factory=list)


class ChatCompletionLogProbs(BaseModel):
    content: Optional[List[ChatCompletionLogProbsContent]] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    logprobs: Optional[ChatCompletionLogProbs] = None
    finish_reason: Optional[str] = "stop"
    stop_reason: Optional[Union[int, str]] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: UsageInfo
    prompt_logprobs: Optional[List[Optional[Dict[int, Logprob]]]] = None


class DeltaMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    logprobs: Optional[ChatCompletionLogProbs] = None
    finish_reason: Optional[str] = None
    stop_reason: Optional[Union[int, str]] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionResponseStreamChoice]
    usage: Optional[UsageInfo] = Field(default=None)


class CompletionLogProbs(BaseModel):
    text_offset: List[int] = Field(default_factory=list)
    token_logprobs: List[Optional[float]] = Field(default_factory=list)
    tokens: List[str] = Field(default_factory=list)
    top_logprobs: List[Optional[Dict[str, float]]] = Field(default_factory=list)


class CompletionResponseChoice(BaseModel):
    index: int
    text: str
    logprobs: Optional[CompletionLogProbs] = None
    finish_reason: Optional[str] = None
    stop_reason: Optional[Union[int, str]] = Field(
        default=None,
        description=(
            "The stop string or token id that caused the completion " "to stop, None if the completion finished for some other reason " "including encountering the EOS token"
        ),
    )
    prompt_logprobs: Optional[List[Optional[Dict[int, Logprob]]]] = None


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionResponseChoice]
    usage: UsageInfo


class CompletionResponseStreamChoice(BaseModel):
    index: int
    text: str
    logprobs: Optional[CompletionLogProbs] = None
    finish_reason: Optional[str] = None
    stop_reason: Optional[Union[int, str]] = Field(
        default=None,
        description=(
            "The stop string or token id that caused the completion " "to stop, None if the completion finished for some other reason " "including encountering the EOS token"
        ),
    )


class CompletionStreamResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[CompletionResponseStreamChoice]
    usage: Optional[UsageInfo] = Field(default=None)


def build_vllm_chute(
    username: str,
    model_name: str,
    node_selector: NodeSelector,
    image: str | Image = VLLM,
    readme: str = "",
    engine_args: Dict[str, Any] = {},
):
    # Semi-optimized defaults for code starts (but not overall perf once hot).
    defaults = {
        "enforce_eager": True,
        "num_scheduler_steps": 1,
        "multi_step_stream_outputs": True,
        "enable_chunked_prefill": False,
        "enable_prefix_caching": False,
        "disable_log_stats": True,
        "disable_custom_all_reduce": True,
    }
    for key, value in defaults.items():
        if key not in engine_args:
            engine_args[key] = value

    async def initialize_vllm():
        nonlocal engine_args
        nonlocal model_name

        # Imports here to avoid needing torch/vllm/etc. to just perform inference/build remotely.
        import torch
        import multiprocessing
        from vllm import AsyncEngineArgs, AsyncLLMEngine
        import vllm.entrypoints.openai.api_server as vllm_api_server
        from vllm.entrypoints.logger import RequestLogger
        from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
        from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion
        from vllm.entrypoints.openai.serving_engine import BaseModelPath

        # Reset torch.
        torch.cuda.empty_cache()
        torch.cuda.init()
        torch.cuda.set_device(0)
        multiprocessing.set_start_method("spawn", force=True)

        # Configure engine arguments
        gpu_count = int(os.getenv("CUDA_DEVICE_COUNT", str(torch.cuda.device_count())))
        engine_args = AsyncEngineArgs(
            model=model_name,
            tensor_parallel_size=gpu_count,
            **engine_args,
        )

        # Initialize engine directly in the main process
        engine = AsyncLLMEngine.from_engine_args(engine_args)
        model_config = await engine.get_model_config()

        request_logger = RequestLogger(max_log_len=1024)
        base_model_paths = [
            BaseModelPath(name=model_name, model_path=model_name),
        ]

        # self.include_router(vllm_api_server.router)
        vllm_api_server.chat = lambda s: OpenAIServingChat(
            engine,
            model_config=model_config,
            base_model_paths=base_model_paths,
            chat_template=None,
            response_role="assistant",
            lora_modules=[],
            prompt_adapters=[],
            request_logger=request_logger,
            return_tokens_as_token_ids=True,
        )
        vllm_api_server.completion = lambda s: OpenAIServingCompletion(
            engine,
            model_config=model_config,
            base_model_paths=base_model_paths,
            lora_modules=[],
            prompt_adapters=[],
            request_logger=request_logger,
            return_tokens_as_token_ids=True,
        )
