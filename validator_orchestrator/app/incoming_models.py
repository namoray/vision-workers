"""
The naming convention is super important to adhere too!

Keep it as SynapseNameBase / SynapseNameIncoming / SynapseNameOutgoing
"""

from typing import List, Optional
from pydantic import BaseModel, Field


from app import utility_models


class ImageGenerationBase(BaseModel):
    cfg_scale: float = Field(..., description="Scale for the configuration")
    steps: int = Field(
        ..., description="Number of steps in the image generation process"
    )
    seed: int = Field(
        ...,
        description="Random seed for generating the image. NOTE: THIS CANNOT BE SET, YOU MUST PASS IN 0, SORRY!",
    )
    engine: utility_models.modelEnum = Field(
        default=utility_models.modelEnum.PROTEUS.value,
        description="The engine to use for image generation",
    )

    class Config:
        use_enum_values = True


class TextToImageIncoming(ImageGenerationBase):
    text_prompts: List[utility_models.TextPrompt] = Field(
        [], description="Prompts for the image generation", title="text_prompts"
    )

    height: int = Field(..., description="Height of the generated image")
    width: int = Field(..., description="Width of the generated image")


class ImageToImageIncoming(ImageGenerationBase):
    init_image: Optional[str] = Field(
        ..., description="The base64 encoded image", title="init_image"
    )
    text_prompts: List[utility_models.TextPrompt] = Field(
        [], description="Prompts for the image generation", title="text_prompts"
    )
    image_strength: float = Field(0.25, description="The strength of the init image")

    height: Optional[int] = Field(None, description="Height of the generated image")
    width: Optional[int] = Field(None, description="Width of the generated image")


class InpaintIncoming(BaseModel):
    init_image: Optional[str] = Field(
        ..., description="The base64 encoded image", title="init_image"
    )
    text_prompts: List[utility_models.TextPrompt] = Field(
        [], description="Prompts for the image generation", title="text_prompts"
    )

    mask_image: Optional[str] = Field(
        None, description="The base64 encoded mask", title="mask_source"
    )
    steps: int = Field(
        ..., description="Number of steps in the image generation process"
    )
    seed: int = Field(
        ...,
        description="Random seed for generating the image. NOTE: THIS CANNOT BE SET, YOU MUST PASS IN 0, SORRY!",
    )

    class Config:
        use_enum_values = True


class UpscaleIncoming(BaseModel):
    image: Optional[str] = Field(
        ..., description="The base64 encoded image", title="image"
    )


class AvatarIncoming(BaseModel):
    text_prompts: List[utility_models.TextPrompt] = Field(
        ..., description="Prompts for the image generation", title="text_prompts"
    )
    init_image: Optional[str] = Field(
        ..., description="The base64 encoded image", title="image"
    )
    ipadapter_strength: float = Field(..., description="The strength of the init image")
    control_strength: float = Field(..., description="The strength of the init image")
    height: int = Field(..., description="Height of the generated image")
    width: int = Field(..., description="Width of the generated image")
    steps: int = Field(
        ..., description="Number of steps in the image generation process"
    )
    seed: int = Field(
        ...,
        description="Random seed for generating the image. NOTE: THIS CANNOT BE SET, YOU MUST PASS IN 0, SORRY!",
    )

    class Config:
        use_enum_values = True


# OUTPAINTING


# CLIP EMBEDDINGS
class ClipEmbeddingsIncoming(BaseModel):
    image_b64s: Optional[List[str]] = Field(
        None,
        description="The image b64s",
        title="image_b64s",
    )


# SOTA
class SotaIncoming(BaseModel):
    prompt: str


class ChatIncoming(BaseModel):
    messages: list[utility_models.Message] = Field(...)

    top_p: float = Field(
        1,
        title="Top P",
        description="The probability for text generation.",
        example=1,
    )

    temperature: float = Field(
        default=...,
        title="Temperature",
        description="Temperature for text generation.",
    )

    max_tokens: int = Field(
        500, title="Max Tokens", description="Max tokens for text generation."
    )

    seed: int = Field(
        default=...,
        title="Seed",
        description="Seed for text generation.",
    )

    model: str = Field(...)

    class Config:
        use_enum_values = True
