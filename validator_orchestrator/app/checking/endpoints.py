from fastapi import APIRouter

from app import models
from app.checking import scoring
from app import server_management
from app.settings import task_configs
from fastapi import Depends
from asyncio import Lock
from app import dependencies
from loguru import logger

router = APIRouter(
    prefix="",
    tags=["check-result"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def root():
    return {"message": "Hello World"}


# One check result at a time please
lock = Lock()
last_task = None


@router.post("/check-result")
async def check_result(
    request: models.CheckResultsRequest,
    server_manager: server_management.ServerManager = Depends(
        dependencies.get_server_manager
    ),
):
    async with lock:
        global last_task

        logger.info("Checking a result!... 🫡")
        task_config = task_configs.tasks[request.task]
        server_needed = task_config.server_needed
        await server_manager.start_server(server_needed)
        logger.debug(f"Task config: {task_config}")
        load_model_config = task_config.load_model_config
        if load_model_config is not None:
            load_model_config_dumped = task_config.load_model_config.model_dump()
            # If this is the first time loading this model, force reload it, incase it has been updated
            if last_task != request.task:
                load_model_config_dumped["force_reload"] = True
            await server_manager.load_model(load_model_config_dumped)

        last_task = request.task
        return await scoring.score_results(
            result=request.result,
            task_config=task_config,
            synapse=request.synapse,
        )