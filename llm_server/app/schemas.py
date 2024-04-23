from pydantic import BaseModel, Field
from typing import Optional
from app import models


class LoadModelRequest(BaseModel):
    model: str = Field(..., example="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ")
    tokenizer: Optional[str] = Field(
        None, example="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ"
    )
    half_precision: Optional[bool] = Field(
        True,
        example=True,
        description="Whether to use half precision - dont for the nous finetinues!",
    )
    revision: Optional[str] = Field(None, example="gptq-8bit-128g-actorder_True")
    force_reload: bool = Field(False)


class LoadModelResponse(BaseModel):
    success: bool


class TextRequestModel(models.RequestInfo): ...
