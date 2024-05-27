import fastapi
from fastapi import Request, Response, status
from starlette.responses import StreamingResponse
from app import schemas, dependencies
from app.inference import infer
from app.inference.state import EngineState  # Import EngineState from state.py
import transformers

async def load_model(
    request: schemas.LoadModelRequest,
    EngineState: EngineState = fastapi.Depends(dependencies.get_engine_state),
) -> schemas.LoadModelResponse:
    model = request.model
    tokenizer = request.tokenizer
    revision = request.revision
    force_reload = request.force_reload

    await EngineState.load_model_and_tokenizer(
        model, revision, tokenizer, request.half_precision, force_reload
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
        async_text_generator = infer.infer(
            request, EngineState, EngineState.toxic_checker
        )
        return StreamingResponse(async_text_generator, media_type="text/plain")
    except Exception as e:
        return Response(
            content=f'{{"error": "{str(e)}"}}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )

router = fastapi.APIRouter(
    prefix="",
    tags=["LLM"],
    responses={404: {"description": "Not found"}},
)

router.add_api_route(
    "/load_model",
    load_model,  # Replace with your actual function
    methods=["POST"],
    response_model=schemas.LoadModelResponse,
    responses={
        400: {"description": "Invalid request format or missing fields"},
        200: {"description": "Model loaded successfully"},
    },
)

router.add_api_route(
    "/generate_text",
    generate_text,  # Replace with your actual function
    methods=["POST"],
    response_model=schemas.TextRequestModel,
    responses={
        400: {"description": "Invalid request format or missing prompt"},
        500: {"description": "Internal server error"},
        200: {"description": "Text generated successfully"},
    },
)