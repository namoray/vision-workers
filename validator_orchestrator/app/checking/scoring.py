# i think i should just be posting to a checking servier to do all of this & return me what the details

from datetime import datetime
from typing import Callable, Dict
from typing import Any
from app.core import constants as cst
from app.core import models
from loguru import logger
import importlib


def _import_function(function_name: str) -> Callable | None:
    """Import a function from app.checking.functions module"""
    try:
        module_name = "app.checking.functions"
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing function {function_name}: {e}")
        return None


async def score_results(
    result: models.QueryResult,
    payload: dict[str, Any],
    task_config: models.OrchestratorServerConfig,
) -> models.TaskResult:

    axon_scores: Dict[int, float] = {}

    if result.formatted_response is None:
        logger.info(f"Got no formatted response. Axon scores: {axon_scores}")
        return models.TaskResult(axon_scores=axon_scores, timestamp=datetime.now())

    logger.info("Checking scores with server...")
    func = _import_function(task_config.checking_function)
    if func is None:
        logger.error(f"Could not import function {task_config.checking_function}")
        return models.TaskResult(axon_scores=axon_scores, timestamp=datetime.now())
    base_score: float = await func(result, payload, task_config)

    if base_score is None:
        logger.info(f"Got no base score. Axon scores: {axon_scores}")
        return models.TaskResult(axon_scores=axon_scores, timestamp=datetime.now())

    axon_scores[result.node_id] = base_score

    logger.info(f"Got Axon scores: {axon_scores}")

    return models.TaskResult(axon_scores=axon_scores, timestamp=datetime.now())
