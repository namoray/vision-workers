from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import constants as cst


class EngineEnum(str, Enum):
    DREAMSHAPER = "dreamshaper"
    PROTEUS = "proteus"
    PLAYGROUND = "playground"


class Txt2ImgBase(BaseModel):
    text_prompts: List[Dict[str, Any]] = Field(
        ..., example=[{"text": "dolphin", "weight": 1.0}]
    )
    steps: int = Field(
        cst.DEFAULT_STEPS,
        description="Number of inference steps, higher for more quality but increased generation time",
        gt=4,
        lt=50,
    )
    engine: EngineEnum = Field(
        EngineEnum.PROTEUS.value, description="The engine to use for image generation"
    )
    cfg_scale: float = Field(
        cst.DEFAULT_CFG, description="Guidance scale", gt=1.5, lt=12
    )
    height: int = Field(
        cst.DEFAULT_HEIGHT,
        description="Height of the output image in pixels",
        gt=512,
        lt=2048,
    )
    width: int = Field(
        cst.DEFAULT_WIDTH,
        description="Width of the output image in pixels",
        gt=512,
        lt=2048,
    )
    seed: int = Field(
        ..., description="Seed value for deterministic outputs", ge=0
    )


class Img2ImgBase(BaseModel):
    text_prompts: List[Dict[str, Any]] = Field(
        ..., example=[{"text": "hello", "weight": 1.0}]
    )
    init_image: str
    engine: EngineEnum = Field(
        EngineEnum.PROTEUS.value, description="The engine to use for image generation"
    )
    image_strength: float = Field(
        cst.DEFAULT_IMAGE_STRENGTH,
        description="Image strength of the generated image with respect to the original image",
        gt=0.1,
        lt=1,
    )
    steps: int = Field(
        cst.DEFAULT_STEPS,
        description="Number of inference steps, higher for more quality but increased generation time",
        gt=4,
        lt=50,
    )
    cfg_scale: float = Field(
        cst.DEFAULT_CFG, description="Guidance scale", gt=1.5, lt=12
    )
    seed: int = Field(
        ..., description="Seed value for deterministic outputs", ge=0
    )


class UpscaleBase(BaseModel):
    init_image: str


class AvatarBase(BaseModel):
    text_prompts: List[Dict[str, Any]]
    init_image: str
    ipadapter_strength: float = Field(
        cst.DEFAULT_IP_STRENGTH,
        description="IP Adapter strength, increase for more face coherence, works best on default",
        gt=0.1,
        le=1,
    )
    control_strength: float = Field(
        cst.DEFAULT_CONTROL_STRENGTH,
        description="Control strength, increase for more face coherence, works best on default",
        gt=0.1,
        le=1.01,
    )
    steps: int = Field(
        cst.DEFAULT_STEPS_AVATAR,
        description="Number of inference steps, higher for more quality but increased generation time",
        gt=4,
        lt=50,
    )
    height: int = Field(
        cst.DEFAULT_HEIGHT,
        description="Height of the output image in pixels",
        gt=512,
        lt=2048,
    )
    width: int = Field(
        cst.DEFAULT_WIDTH,
        description="Width of the output image in pixels",
        gt=512,
        lt=2048,
    )
    seed: int = Field(
        ..., description="Seed value for deterministic outputs", ge=0
    )


class InpaintingBase(BaseModel):
    text_prompts: List[Dict[str, Any]]
    init_image: str
    mask_image: str
    steps: int = Field(
        cst.DEFAULT_STEPS_INPAINT,
        description="Number of inference steps, higher for more quality but increased generation time",
        gt=4,
        lt=50,
    )
    cfg_scale: float = Field(
        cst.DEFAULT_CFG_INPAINT, description="Guidance scale", gt=1.5, lt=12
    )
    seed: int = Field(
        ..., description="Seed value for deterministic outputs", ge=0
    )


class OutpaintingBase(BaseModel):
    text_prompts: List[Dict[str, Any]]
    init_image: str
    text_prompts: List[Dict[str, Any]] = Field(
        default=[{"text": "", "weight": 1}],
        description="Text prompts to guide the generation process",
    )
    pad_values: dict = Field(
        default={"left": 104, "right": 104, "top": 104, "bottom": 104},
        description="Dictionary specifying padding in pixels for each side of the image for expansion. Format: {'left': int, 'right': int, 'top': int, 'bottom': int}",
    )
    steps: int = Field(
        cst.DEFAULT_STEPS_INPAINT,
        description="Number of inference steps, higher for more quality but increased generation time",
        gt=4,
        lt=50,
    )
    cfg_scale: float = Field(
        cst.DEFAULT_CFG_INPAINT, description="Guidance scale", gt=1.5, lt=12
    )
    seed: int = Field(
        ..., description="Seed value for deterministic outputs", ge=0
    )


class ClipEmbeddingsBase(BaseModel):
    image_b64s: Optional[List[str]] = Field(
        None,
        description="The image b64s",
        title="image_b64s",
    )


class ImageHashes(BaseModel):
    average_hash: str = ""
    perceptual_hash: str = ""
    difference_hash: str = ""
    color_hash: str = ""


class ImageResponseBody(BaseModel):
    image_b64: Optional[str] = None
    is_nsfw: Optional[bool] = None
    clip_embeddings: Optional[List[float]] = None
    image_hashes: Optional[ImageHashes] = None


class ClipEmbeddingsResponse(BaseModel):
    clip_embeddings: Optional[List[List[float]]] = None


class ClipEmbeddingsTextBase(BaseModel):
    text_prompt: str


class ClipEmbeddingsTextResponse(BaseModel):
    text_embedding: Optional[List[float]] = None
