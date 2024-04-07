from fastapi import FastAPI
import base_model
import inference
import traceback
from typing import Callable
from functools import wraps
from starlette.responses import PlainTextResponse

app = FastAPI()


def handle_request_errors(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            tb_str = traceback.format_exc()
            return {"error": str(e), "traceback": tb_str}

    return wrapper


@app.get("/")
async def home():
    return PlainTextResponse("Image!")


@app.post("/txt2img")
@handle_request_errors
async def txt2img(request_data: base_model.Txt2ImgBase) -> base_model.ImageResponseBody:
    return await inference.txt2img_infer(request_data)


@app.post("/img2img")
@handle_request_errors
async def img2img(request_data: base_model.Img2ImgBase) -> base_model.ImageResponseBody:
    return await inference.img2img_infer(request_data)


@app.post("/upscale")
@handle_request_errors
async def upscale(request_data: base_model.UpscaleBase) -> base_model.ImageResponseBody:
    return await inference.upscale_infer(request_data)


@app.post("/avatar")
@handle_request_errors
async def avatar(
    request_data: base_model.AvatarBase,
) -> base_model.ImageResponseBody:
    return await inference.avatar_infer(request_data)


@app.post("/inpaint")
@handle_request_errors
async def inpaint(
    request_data: base_model.InpaintingBase,
) -> base_model.ImageResponseBody:
    return await inference.inpainting_infer(request_data)


@app.post("/outpaint")
@handle_request_errors
async def outpaint(
    request_data: base_model.OutpaintingBase,
) -> base_model.ImageResponseBody:
    return await inference.outpainting_infer(request_data)


@app.post("/clip-embeddings")
@handle_request_errors
async def clip_embeddings(
    request_data: base_model.ClipEmbeddingsBase,
) -> base_model.ClipEmbeddingsResponse:
    embeddings = await inference.get_clip_embeddings(request_data)
    return base_model.ClipEmbeddingsResponse(clip_embeddings=embeddings)


@app.post("/clip-embeddings-text")
@handle_request_errors
async def clip_embeddings_text(
    request_data: base_model.ClipEmbeddingsTextBase,
) -> base_model.ClipEmbeddingsTextResponse:
    embedding = await inference.get_clip_embeddings_text(request_data)
    return base_model.ClipEmbeddingsTextResponse(text_embedding=embedding)


if __name__ == "__main__":
    import uvicorn
    import os

    if "CUBLAS_WORKSPACE_CONFIG" not in os.environ:
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    import torch

    # Below doens't do much except cause major issues with mode loading and unloading
    torch.use_deterministic_algorithms(False)

    uvicorn.run(app, host="0.0.0.0", port=6919)
