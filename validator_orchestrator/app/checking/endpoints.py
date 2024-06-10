from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Union
from uuid import uuid4
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

task_status: Dict[str, Union[str, Dict]] = {}
lock = Lock()
current_task_id = None


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.post("/check-result")
async def check_result(
    request: models.CheckResultsRequest,
    background_tasks: BackgroundTasks,
    server_manager: server_management.ServerManager = Depends(dependencies.get_server_manager),
):
    global current_task_id
    
    # Check if there's an ongoing task
    if current_task_id is not None:
        if task_status.get(current_task_id) == "Processing":
            return {"message": "A task is already WIP"}

    # If no task is in progress, proceed
    task_id = str(uuid4())
    current_task_id = task_id
    task_status[task_id] = "Processing"
    background_tasks.add_task(process_check_result, task_id, request, server_manager)
    return {"task_id": task_id}


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
            task_status[task_id] = result  # Save the result as the task status
        except Exception as e:
            error_message = f"Error processing task {task_id}: {str(e)}"
            logger.error(error_message)
            task_status[task_id] = {"status": "Failed", "error": error_message}
        finally:
            current_task_id = None  # Reset the current task ID when done


@router.get("/check-task/{task_id}")
async def check_task(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = task_status[task_id]
    if isinstance(status, str) and status == "Processing":
        return {"task_id": task_id, "status": "Processing"}
    return {"task_id": task_id, "result": status}