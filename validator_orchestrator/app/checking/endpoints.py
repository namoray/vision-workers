from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict
from uuid import uuid4
from app import models
from app.checking import scoring
from app import server_management
from app.settings import task_configs
from fastapi import Depends
from asyncio import Lock, create_task, sleep
from app import dependencies
from loguru import logger
import traceback
from datetime import datetime, timedelta

router = APIRouter(
    prefix="",
    tags=["check-result"],
    responses={404: {"description": "Not found"}},
)

task_status: Dict[str, str] = {}
task_results: Dict[str, Dict] = {}
lock = Lock()
current_task_id = None
RESULT_EXPIRY_TIME = timedelta(hours=1)


@router.on_event("startup")
async def startup_event():
    create_task(cleanup_expired_tasks())


async def cleanup_expired_tasks():
    while True:
        await sleep(3600)
        now = datetime.now()
        expired_tasks = [task_id for task_id, data in task_results.items() if now - data["timestamp"] > RESULT_EXPIRY_TIME]
        for task_id in expired_tasks:
            task_results.pop(task_id, None)
        logger.info(f"Cleanup: Removed {len(expired_tasks)} expired tasks")


@router.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    return {"message": "Hello World"}


@router.post("/check-result", response_model=models.CheckResultResponse)
async def check_result(
    request: models.CheckResultsRequest,
    background_tasks: BackgroundTasks,
    server_manager: server_management.ServerManager = Depends(dependencies.get_server_manager),
) -> models.CheckResultResponse:
    global current_task_id
    
    if current_task_id is not None:
        if task_status.get(current_task_id) == "Processing":
            return models.CheckResultResponse(task_id=current_task_id, status="A task is already WIP")

    task_id = str(uuid4())
    current_task_id = task_id
    task_status[task_id] = "Processing"
    background_tasks.add_task(process_check_result, task_id, request, server_manager)
    return models.CheckResultResponse(task_id=task_id, status="Processing")


async def process_check_result(task_id: str, request: models.CheckResultsRequest, server_manager: server_management.ServerManager):
    global current_task_id, last_task
    async with lock:
        try:
            logger.info("Checking a result!... 🫡")
            task_config = task_configs.tasks[request.task]
            server_needed = task_config.server_needed
            await server_manager.start_server(server_needed)
            logger.debug(f"Task config: {task_config}")
            load_model_config = task_config.load_model_config
            if load_model_config is not None:
                load_model_config_dumped = task_config.load_model_config.model_dump()
                if last_task != request.task:
                    load_model_config_dumped["force_reload"] = True
                await server_manager.load_model(load_model_config_dumped)
            last_task = request.task
            result = await scoring.score_results(
                result=request.result,
                task_config=task_config,
                synapse=request.synapse,
            )
            task_results[task_id] = {"result": result, "timestamp": datetime.now()}
        except Exception as e:
            error_message = f"Error processing task {task_id}: {str(e)}"
            error_traceback = traceback.format_exc()
            logger.error(f"{error_message}\n{error_traceback}")
            task_results[task_id] = {"status": "Failed", "error": error_message, "traceback": error_traceback, "timestamp": datetime.now()}
        finally:
            task_status.pop(task_id, None)
            current_task_id = None


@router.get("/check-task/{task_id}", response_model=models.CheckTaskResponse)
async def check_task(task_id: str) -> models.CheckTaskResponse:
    if task_id not in task_status and task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found (or Task result got expired)")
    
    if task_id in task_status:
        return models.CheckTaskResponse(task_id=task_id, status=task_status[task_id], result=None)
    
    result = task_results.pop(task_id, None)
    if result:
        return models.CheckTaskResponse(task_id=task_id, result=result, status=None)
    
    raise HTTPException(status_code=404, detail="Task retrieval failed")