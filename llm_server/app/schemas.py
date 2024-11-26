from pydantic import BaseModel, Field
from typing import Optional
from app import models


class LoadModelRequest(BaseModel):
    model: str = Field(..., example="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ")
    tokenizer: Optional[str] = Field(None, example="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ")
    half_precision: Optional[bool] = Field(
        True,
        example=True,
        description="Whether to use half precision - dont for the nous finetinues!",
    )
    revision: Optional[str] = Field(None, example="gptq-8bit-128g-actorder_True")
    force_reload: bool = Field(False)
    gpu_memory_utilization: float = Field(0.8, example="0.85")
    max_model_len: Optional[int] = Field(None, example="8000")
    tensor_parallel_size: Optional[int] = Field(1, example="1")
    num_scheduler_steps: Optional[int] = Field(1, example="1")


class LoadModelResponse(BaseModel):
    success: bool


class TextRequestModel(models.RequestInfo): ...

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.9
    top_p: float = 0.95
    top_k: int = 5
    prompt_logprobs: int = 10
    number_of_logprobs: int = 1
    class Config:
        extra = "allow"