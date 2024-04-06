

from pydantic import BaseModel, Field
from typing import Optional
from app import models


class LoadModelRequest(BaseModel):
    model: str = Field(..., example="NousResearch/Hermes-2-Pro-Mistral-7B")
    tokenizer: Optional[str] = Field(None, example="NousResearch/Hermes-2-Pro-Mistral-7B")
    half_precision: Optional[bool] = Field(True, example=True, description="Whether to use half precision - dont for the nous finetinues!")
    revision: Optional[str] = Field(None, example="gptq-8bit-128g-actorder_True")

class LoadModelResponse(BaseModel):
    success: bool


class TextRequestModel(models.RequestInfo):
    ...