import fastapi
from fastapi import Request, Response, status
from starlette.responses import StreamingResponse
from app import schemas, dependencies
from app.inference import infer
from app.inference.state import EngineState
from app import models
import transformers
from vllm import SamplingParams
import json
from typing import Dict, Any
from loguru import logger

async def load_model(
    request: schemas.LoadModelRequest,
    EngineState: EngineState = fastapi.Depends(dependencies.get_engine_state),
) -> schemas.LoadModelResponse:
    model = request.model
    tokenizer = request.tokenizer
    revision = request.revision
    force_reload = request.force_reload
    gpu_memory_utilization = request.gpu_memory_utilization
    max_model_len = request.max_model_len
    tensor_parallel_size = request.tensor_parallel_size
    num_scheduler_steps = request.num_scheduler_steps

    await EngineState.load_model_and_tokenizer(
        model, revision, tokenizer, request.half_precision, 
        force_reload, gpu_memory_utilization, max_model_len, 
        tensor_parallel_size, num_scheduler_steps
    )
    return schemas.LoadModelResponse(success=True)


async def generate_text(
    raw_request: Request,
    request: schemas.TextRequestModel,
    EngineState: EngineState = fastapi.Depends(dependencies.get_engine_state),
):
    if not EngineState.model_loaded:
        return Response(
            content='{"error": "No model has been loaded, please use the load_model endpoint to load a model"}',
            status_code=status.HTTP_400_BAD_REQUEST,
            media_type="application/json",
        )

    transformers.set_seed(request.seed)

    try:
        async_text_generator = infer.infer(request, EngineState, EngineState.toxic_checker)
        return StreamingResponse(async_text_generator, media_type="text/plain")
    except Exception as e:
        return Response(
            content=f'{{"error": "{str(e)}"}}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )
    
async def completion(
    request: schemas.CompletionRequest,
    EngineState: EngineState = fastapi.Depends(dependencies.get_engine_state),
) -> Response:
    if not EngineState.model_loaded:
        return Response(
            content='{"error": "No model has been loaded"}',
            status_code=status.HTTP_400_BAD_REQUEST,
            media_type="application/json",
        )

    try:
        request_info = models.RequestInfo(**request.dict(), stream=False)
        response_stream = EngineState.forward_request(request_info)
        
        response_lines = []
        async for line in response_stream:
            if line and not line.endswith("[DONE]\n\n"):
                response_lines.append(line)

        if response_lines:
            last_response = response_lines[-1]
            json_str = last_response.replace("data: ", "").strip()
            response_data = json.loads(json_str)
            output_data = {
                "choices": [{
                    "text": response_data["choices"][0]["delta"]["content"],
                    "logprobs": response_data["choices"][0]["logprobs"]["content"],
                    "prompt_logprobs": response_data["choices"][0].get("prompt_logprobs", {})
                }]
            }

            return Response(
                content=json.dumps(output_data),
                status_code=status.HTTP_200_OK,
                media_type="application/json"
            )
        
        raise ValueError("No response received")
        
    except Exception as e:
        logger.exception(f"Error in completion endpoint: {str(e)}")
        return Response(
            content=f'{{"error": "{str(e)}"}}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )

router = fastapi.APIRouter(
    prefix="",
    tags=["LLM"],
    responses={404: {"description": "Not found"}},
)

router.add_api_route(
    "/vali-completions",
    completion,
    methods=["POST"],
    response_model=None,
    responses={
        400: {"description": "Invalid request format or missing prompt"},
        500: {"description": "Internal server error"},
        200: {"description": "Completion generated successfully"},
    },
)

router.add_api_route(
    "/load_model",
    load_model,
    methods=["POST"],
    response_model=schemas.LoadModelResponse,
    responses={
        400: {"description": "Invalid request format or missing fields"},
        200: {"description": "Model loaded successfully"},
    },
)

router.add_api_route(
    "/generate_text",
    generate_text,
    methods=["POST"],
    response_model=schemas.TextRequestModel,
    responses={
        400: {"description": "Invalid request format or missing prompt"},
        500: {"description": "Internal server error"},
        200: {"description": "Text generated successfully"},
    },
)

router.add_api_route(
    "/chat/completions",
    generate_text,
    methods=["POST"],
    response_model=schemas.TextRequestModel,
    responses={
        400: {"description": "Invalid request format or missing prompt"},
        500: {"description": "Internal server error"},
        200: {"description": "Text generated successfully"},
    },
)
