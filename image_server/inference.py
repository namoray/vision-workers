from typing import List
import base_model
import constants as cst
import utils.api_gate as api_gate
from utils import base64_utils
from payload import PayloadModifier
from clip_embeddings.clip_manager import ClipEmbeddingsProcessor
import torch
from utils import misc
import os
import clip


payload_modifier = PayloadModifier()
clip_emb_processor = ClipEmbeddingsProcessor()


async def txt2img_infer(
    infer_props: base_model.Txt2ImgBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_txt2img(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def img2img_infer(
    infer_props: base_model.Img2ImgBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_img2img(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def upscale_infer(
    infer_props: base_model.UpscaleBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_upscale(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def avatar_infer(
    infer_props: base_model.AvatarBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_avatar(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def inpainting_infer(
    infer_props: base_model.InpaintingBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_inpaint(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def outpainting_infer(
    infer_props: base_model.OutpaintingBase,
) -> base_model.ImageResponseBody:
    payload = payload_modifier.modify_outpaint(infer_props)
    image = api_gate.generate(payload)[0]
    return await misc.take_image_and_return_formatted_response_body(image)


async def get_clip_embeddings(
    infer_props: base_model.ClipEmbeddingsBase,
) -> List[List[float]]:
    clip_model, clip_processor = clip_emb_processor.get_clip_resources()
    clip_device = clip_emb_processor.clip_device
    images = [
        base64_utils.base64_to_image(img_b64) for img_b64 in infer_props.image_b64s
    ]
    images = [clip_processor(image) for image in images]
    images_tensor = torch.stack(images).to(clip_device)

    with torch.no_grad():
        image_embeddings = clip_model.encode_image(images_tensor)

    image_embeddings = image_embeddings.cpu().numpy().tolist()
    return image_embeddings


async def get_clip_embeddings_text(
    infer_props: base_model.ClipEmbeddingsTextBase,
) -> List[float]:
    clip_model, _ = clip_emb_processor.get_clip_resources()
    clip_device = clip_emb_processor.clip_device

    texts_tensor = clip.tokenize([infer_props.text_prompt]).to(clip_device)

    with torch.no_grad():
        text_embeddings = clip_model.encode_text(texts_tensor)

    text_embedding = text_embeddings.cpu().numpy().tolist()[0]
    return text_embedding
