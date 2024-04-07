# i think i should just be posting to a checking servier to do all of this & return me what the details

from typing import Dict
from typing import Any
from app import constants as cst
from app import models
from loguru import logger


async def score_results(
    result: models.QueryResult,
    synapse: Dict[str, Any],
    task_config: models.TaskConfig,
) -> Dict[str, Any]:
    axon_scores: Dict[int, float] = {}
    for failed_axon in result.failed_axon_uids:
        if failed_axon is not None:
            axon_scores[failed_axon] = cst.FAILED_RESPONSE_SCORE

    # All requests failed? Then just return the scores for failed ids
    if result.formatted_response is None:
        return {"axon_scores": axon_scores}

    
    logger.info("Checking scores with server...")
    base_score: float = await task_config.checking_function(
        result, synapse, task_config
    )

    if base_score is None:
        return {"axon_scores": axon_scores}

    speed_mulitplier: float = await task_config.speed_scoring_function(
        result, synapse, task_config
    )

    axon_scores[result.axon_uid] = base_score * speed_mulitplier

    logger.info(f"Got scores: {axon_scores}")

    return {"axon_scores": axon_scores}
