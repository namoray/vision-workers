from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict
from uuid import uuid4
import os
from app.core import models
from app.checking import scoring
from app import server_management
from fastapi import Depends
from app.core import dependencies
from loguru import logger
import traceback
from datetime import datetime
from app.checking.task_manager import task_manager
import asyncio

router = APIRouter(
    prefix="",
    tags=["check-result"],
    responses={404: {"description": "Not found"}},
)

global_async_lock = asyncio.Lock()


@router.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    return {"message": "Hello World"}


@router.post("/check-result")
async def check_result(
    request: models.CheckResultsRequest,
    background_tasks: BackgroundTasks,
    server_manager: server_management.ServerManager = Depends(dependencies.get_server_manager),
) -> models.CheckResultResponse:
    if task_manager.current_task_id is not None:
        return models.CheckResultResponse(
            task_id=task_manager.current_task_id,
            status=models.TaskStatus.Busy,
        )

    task_id = str(uuid4())
    task_manager.current_task_id = task_id
    task_manager.task_status[task_id] = models.TaskStatus.Processing
    background_tasks.add_task(process_check_result, task_id, request, server_manager)
    return models.CheckResultResponse(task_id=task_id, status=models.TaskStatus.Processing)


async def process_check_result(
    task_id: str,
    request: models.CheckResultsRequest,
    server_manager: server_management.ServerManager,
):
    async with global_async_lock:
        try:
            logger.info("Checking a result for server: !... 🫡")
            task_config: models.OrchestratorServerConfig = request.server_config
            logger.debug(f"Config: {task_config}")
            server_needed = task_config.server_needed
            logger.info(f"Server needed: {server_needed}")

            load_model_config = task_config.load_model_config
            await server_manager.start_server(server_needed, load_model_config)

            if load_model_config is not None:
                # TODO: Why is this needed? Slows down checking *alot*
                # if task_manager.last_task_type != task_config.task:
                #     load_model_config_dumped["force_reload"] = True
                await server_manager.load_model(load_model_config, server_name=server_needed.value)

            task_manager.last_task_type = task_config.task

            result = await scoring.score_results(
                result=request.result,
                task_config=task_config,
                payload=request.payload,
            )

            task_manager.task_status[task_id] = models.TaskStatus.Success
            task_manager.task_results[task_id] = result
        except Exception as e:
            error_message = f"Error processing task {task_id}: {str(e)}"
            error_traceback = traceback.format_exc()
            logger.error(f"{error_message}\n{error_traceback}")
            task_manager.task_status[task_id] = models.TaskStatus.Failed
            task_manager.task_results[task_id] = models.TaskResult(
                error=error_message,
                traceback=error_traceback,
                timestamp=datetime.now(),
                result=None,
            )
        finally:
            task_manager.current_task_id = None


@router.get("/check-task/{task_id}", response_model=models.CheckTaskResponse)
async def check_task(task_id: str) -> models.CheckTaskResponse:
    if task_id not in task_manager.task_status and task_id not in task_manager.task_results:
        raise HTTPException(status_code=404, detail="Task not found (or Task result got expired)")

    if task_manager.task_is_processing(task_id):
        return models.CheckTaskResponse(task_id=task_id, status=task_manager.task_status[task_id], result=None)
    else:
        status, result = task_manager.clear_and_return_task_status_and_result(task_id)
        if result:
            return models.CheckTaskResponse(task_id=task_id, result=result, status=status)

    raise HTTPException(status_code=500, detail="Task retrieval failed... how?")


@router.get("/all-task-status")
async def task_statuses() -> models.AllTaskStatusResponse:
    return models.AllTaskStatusResponse(tasks=task_manager.task_status)
