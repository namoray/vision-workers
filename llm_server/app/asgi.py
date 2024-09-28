import contextlib
import importlib
import os

import dotenv
import fastapi
from fastapi.responses import PlainTextResponse
from app.logging import logging
from app import configuration, endpoints
from app.inference import state
import asyncio


# Hide process termination error from logs (when swapping models)
class CancelledErrorFilter:
    def __call__(self, record):
        if record["exception"]:
            exc_type, _, _ = record["exception"]
            if exc_type is asyncio.exceptions.CancelledError:
                return False
        return True


logging.add(lambda msg: None, filter=CancelledErrorFilter())


async def home():
    return PlainTextResponse("LLM")


def get_router(config: configuration.Config, path: str) -> fastapi.routing.APIRouter:
    """
    Attempt to extract a factory at `path`. Then invoke the factory with `config` and return it.
    """
    module = importlib.import_module(path)
    if module is None:
        raise Exception("Unable to import module at {}".format(path))

    router = module.factory(config)
    logging.info("Successfully built router for {}".format(path))
    return router


dotenv.load_dotenv()
config = configuration.Config()

if config.debug:
    for _ in range(3):
        logging.info("STARTING IN DEBUG MODE, THIS BETTER NOT BE PRODUCTION")


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    initial_model = os.getenv("MODEL", None)
    tokenizer = os.getenv("TOKENIZER", None)

    half_precision = os.getenv("HALF_PRECISION", True)
    revision = os.getenv("REVISION", None)
    gpu_memory_utilization = float(os.getenv("GPU_MEMORY_UTILIZATION", 0.75))
    max_model_len = int(os.getenv("MAX_MODEL_LEN", 16_000))
    tensor_parallel_size = int(os.getenv("TENSOR_PARALLEL_SIZE", 1))
    num_scheduler_steps = int(os.getenv("NUM_SCHEDULER_STEPS", 1))

    engine_state = state.EngineState()
    if initial_model is not None:
        await engine_state.load_model_and_tokenizer(
            initial_model,
            revision,
            tokenizer,
            half_precision,
            True,
            gpu_memory_utilization,
            max_model_len,
            tensor_parallel_size,
            num_scheduler_steps
        )

    app.state.model_state = engine_state
    yield


app = fastapi.FastAPI(
    title="Corcel API",
    lifespan=lifespan,
    debug=config.debug,
)

app.state.config = config

app.add_api_route("/", home, include_in_schema=False)
app.include_router(endpoints.router)
