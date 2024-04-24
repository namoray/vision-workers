import contextlib
import importlib
import os

import dotenv
import fastapi
from fastapi.responses import PlainTextResponse
from app.logging import logging
from app import configuration, endpoints
from app.inference import state


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
    use_toxic_checker = os.getenv("TOXIC_CHECKER", None)
    half_precision = os.getenv("HALF_PRECISION", True)
    revision = os.getenv("REVISION", None)

    # TODO: NICER NAME, prob refactor further
    engine_state = state.EngineState()
    if initial_model is not None:
        await engine_state.load_model_and_tokenizer(
            initial_model, revision, tokenizer, half_precision, force_reload=True
        )

    if use_toxic_checker:
        engine_state.load_toxic_checker()
    app.state.engine_state = engine_state
    yield


app = fastapi.FastAPI(
    title="Corcel API",
    lifespan=lifespan,
    debug=config.debug,
)

app.state.config = config

app.add_api_route("/", home, include_in_schema=False)
app.include_router(endpoints.router)
