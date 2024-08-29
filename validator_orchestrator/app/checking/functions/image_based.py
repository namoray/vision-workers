from app.core import models
from typing import Dict, Any, Union
import httpx
from app.core import utility_models
from app.checking import utils as checking_utils
import xgboost as xgb
from loguru import logger

images_are_same_classifier = xgb.XGBClassifier()
images_are_same_classifier.load_model("image_similarity_xgb_model.json")


def _get_image_similarity(
    image_response_body: utility_models.ImageResponseBody,
    expected_image_response: utility_models.ImageResponseBody,
    images_are_same_classifier: xgb.XGBClassifier,
):
    clip_embedding_similiarity = checking_utils.get_clip_embedding_similarity(
        image_response_body.clip_embeddings, expected_image_response.clip_embeddings
    )
    hash_distances = checking_utils.get_hash_distances(
        image_response_body.image_hashes, expected_image_response.image_hashes
    )
 
    probability_same_image_xg = images_are_same_classifier.predict_proba(
        [hash_distances]
    )[0][1]

    # MODEL has a very low threshold
    if probability_same_image_xg > 0.025:
        score = 1
    else:
        score = clip_embedding_similiarity**2

    return score


async def _query_endpoint_for_image_response(
    endpoint: str, data: Dict[str, Any]
) -> utility_models.ImageResponseBody:
    async with httpx.AsyncClient(timeout=60 * 2) as client:
        logger.info(f"Querying : {endpoint}")
        response = await client.post(endpoint, json=data)
        logger.info(response.status_code)
        return utility_models.ImageResponseBody(**response.json())


async def check_image_result(
    result: models.QueryResult, payload: dict, task_config: models.TaskConfig
) -> Union[float, None]:
    image_response_body = utility_models.ImageResponseBody(**result.formatted_response)

    if (
        image_response_body.image_b64 is None
        and image_response_body.clip_embeddings is None
        and image_response_body.image_hashes is None
        and image_response_body.is_nsfw is None
    ):
        logger.error(f"For some reason Everything is none! {image_response_body}")
        return 0

    expected_image_response = await _query_endpoint_for_image_response(
        task_config.endpoint, payload
    )

    if expected_image_response.clip_embeddings is None:
        logger.error(f"For some reason Everything is none! {expected_image_response}")
        return None

    if expected_image_response.is_nsfw != image_response_body.is_nsfw:
        return 0

    else:
        return _get_image_similarity(
            image_response_body,
            expected_image_response,
            images_are_same_classifier,
        )
