from fastapi import APIRouter
from app.settings import task_configs
from app import models

router = APIRouter()


async def get_synthetic_data(
    data: models.SyntheticGenerationRequest
):
    task_config = task_configs.tasks[data.task]
    synthetic_generation_function = task_config.synthetic_generation_function
    synthetic_generation_params = task_config.synthetic_generation_params

    return await synthetic_generation_function(**synthetic_generation_params)


router.add_api_route(
    path="/get-synthetic-data",
    tags=["synthetic"],
    endpoint=get_synthetic_data,
    methods=["POST"],
)
