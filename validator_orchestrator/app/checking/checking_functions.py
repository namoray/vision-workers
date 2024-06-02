from app import models
from typing import Dict, Any, List, Union
import httpx
import json
import random
from app import utility_models
from app.checking import utils as checking_utils
import xgboost as xgb
import math
from loguru import logger
from PIL import Image
import io
from PIL import UnidentifiedImageError
from typing import Optional
from app.constants import BASE_URL

images_are_same_classifier = xgb.XGBClassifier()
images_are_same_classifier.load_model("image_similarity_xgb_model.json")


##### SOTA ######


async def check_sota_result(
    result: models.QueryResult, synapse: Dict[str, Any], task_config: models.TaskConfig
) -> bool:
    sota_result = utility_models.SotaResponse(**result.formatted_response)

    valid_gojourney_url = checking_utils.validate_gojourney_url(sota_result.image_url)

    if not valid_gojourney_url:
        return 0

    image_bytes = await checking_utils.fetch_image_as_bytes(sota_result.image_url)

    prompt: Optional[str] = synapse.get("prompt", None)
    if prompt is None:
        logger.warning(
            f"Error when fetching image {sota_result.image_url}, can't parse the bytes into a PIL for some reason"
        )
        return 0

    if not image_bytes:
        logger.warning(
            f"Error when fetching image {sota_result.image_url}, can't parse the bytes into a PIL for some reason"
        )
        return 0

    try:
        original_image = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        logger.warning(
            f"Error when fetching image {sota_result.image_url}, can't parse the bytes into a PIL for some reason"
        )

    width, height = original_image.size
    image_1 = original_image.crop((0, 0, width // 2, height // 2))
    image_2 = original_image.crop((width // 2, 0, width, height // 2))
    image_3 = original_image.crop((0, height // 2, width // 2, height))
    image_4 = original_image.crop((width // 2, height // 2, width, height))

    images = [image_1, image_2, image_3, image_4]

    clip_image_embeddings_response: utility_models.ClipEmbeddingsResponse = (
        await query_endpoint_for_clip_response(
            data={"image_b64s": [checking_utils.pil_to_base64(i) for i in images]},
            endpoint=BASE_URL + "/clip-embeddings",
        )
    )

    image_embeddings = clip_image_embeddings_response.clip_embeddings

    split_prompt = prompt.split("--")[0]
    text_embedding_response: utility_models.ClipTextEmbeddingsResponse = (
        await query_endpoint_for_clip_text_response(
            data={"text_prompt": split_prompt},
            endpoint=BASE_URL + "/clip-embeddings-text",
        )
    )

    text_embedding = text_embedding_response.text_embedding

    sims = []
    for image_embedding in image_embeddings:
        embedding_sim = checking_utils.get_clip_embedding_similarity(
            image_embedding, text_embedding
        )
        sims.append(embedding_sim)

    average_sim = sum(sims) / len(sims)

    # Found that 0.21 finds valid images >99.9% of the time, but stops invalid ones > 99% of the time too!
    if average_sim > 0.21:
        return 1

    return 0


### CLIP  ####


async def query_endpoint_for_clip_text_response(
    endpoint: str, data: Dict[str, Any]
) -> utility_models.ClipTextEmbeddingsResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(endpoint, json=data)
        return utility_models.ClipTextEmbeddingsResponse(**response.json())


async def query_endpoint_for_clip_response(
    endpoint: str, data: Dict[str, Any]
) -> utility_models.ClipEmbeddingsResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(endpoint, json=data)
        return utility_models.ClipEmbeddingsResponse(**response.json())


async def check_clip_result(
    result: models.QueryResult, synapse: Dict[str, Any], task_config: models.TaskConfig
) -> Union[float, None]:
    clip_result = utility_models.ClipEmbeddingsResponse(**result.formatted_response)

    expected_clip_response = await query_endpoint_for_clip_response(
        task_config.endpoint, synapse
    )

    if expected_clip_response.clip_embeddings is None:
        logger.error(f"For some reason Everything is none! {expected_clip_response}")
        return None

    total_sim = 0
    for i in range(
        min(
            len(expected_clip_response.clip_embeddings),
            len(clip_result.clip_embeddings),
        )
    ):
        clip_embedding_similiarity = checking_utils.get_clip_embedding_similarity(
            clip_result.clip_embeddings[i], expected_clip_response.clip_embeddings[i]
        )
        total_sim += clip_embedding_similiarity

    normalised_sim = total_sim / max(
        len(expected_clip_response.clip_embeddings), len(clip_result.clip_embeddings)
    )

    return int(normalised_sim > 0.999)


##### Image #######
async def query_endpoint_for_image_response(
    endpoint: str, data: Dict[str, Any]
) -> utility_models.ImageResponseBody:
    async with httpx.AsyncClient(
        timeout=600
    ) as client:  # 10 min timeout due to initial load on some runpod gpus
        response = await client.post(endpoint, json=data)
        logger.info(response.status_code)
        return utility_models.ImageResponseBody(**response.json())


async def check_image_result(
    result: models.QueryResult, synapse: Dict[str, Any], task_config: models.TaskConfig
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

    expected_image_response = await query_endpoint_for_image_response(
        task_config.endpoint, synapse
    )

    if expected_image_response.is_nsfw and image_response_body.is_nsfw:
        return 1

    if expected_image_response.clip_embeddings is None:
        logger.error(f"For some reason Everything is none! {expected_image_response}")
        return None

    # Server got a result but you didn't!
    elif (
        image_response_body.image_b64 is None
        and expected_image_response.image_b64 is not None
    ):
        return 0

    clip_embedding_similiarity = checking_utils.get_clip_embedding_similarity(
        image_response_body.clip_embeddings, expected_image_response.clip_embeddings
    )
    hash_distances = checking_utils.get_hash_distances(
        image_response_body.image_hashes, expected_image_response.image_hashes
    )

    probability_same_image_xg = images_are_same_classifier.predict_proba(
        [hash_distances]
    )[0][1]

    print(probability_same_image_xg, clip_embedding_similiarity)

    # MODEL has a very low threshold
    if probability_same_image_xg > 0.01:
        score = 1
    else:
        score = clip_embedding_similiarity**2

    return score


########### TEXT ###########

async def check_text_result(
    result: models.QueryResult, synapse: Dict[str, Any], task_config: models.TaskConfig
) -> Union[float, None]:
    formatted_response = (
        json.loads(result.formatted_response)
        if isinstance(result.formatted_response, str)
        else result.formatted_response
    )
    miner_chat_responses: List[models.MinerChatResponse] = [
        models.MinerChatResponse(**r) for r in formatted_response
    ]

    # Sort miner_chat_responses by logprobs (largest first, which is smallest probability)
    sorted_responses = sorted(enumerate(miner_chat_responses), key=lambda x: x[1].logprob, reverse=True)
    selected_indices = [i[0] for i in sorted_responses[:10]]

    total_distance = 0
    checks = 0
    synapse["number_of_logprobs"] = 5
    llm_request = models.ChatRequestModel(**synapse)
    llm_request.max_tokens = 1

    for index in range(1, len(miner_chat_responses)):
        if checks >= 10 or index not in selected_indices:
            continue

        text_to_inject_into_assistant_message = "".join(
            [i.text for i in miner_chat_responses[:index]]
        )
        llm_request.messages.append(
            models.Message(
                **{
                    "role": "assistant",
                    "content": text_to_inject_into_assistant_message,
                }
            )
        )
        llm_request.starting_assistant_message = False

        distance = await calculate_distance_for_token(
            task_config, llm_request, miner_chat_responses, index
        )
        checks += 1
        total_distance += distance
        llm_request.messages = llm_request.messages[:-1]

    try:
        average_distance = total_distance / checks
    except:
        print('Error with average distance', total_distance, checks)
        average_distance = 0.1

    def scoring_func(x):
        if x <= 0.03:
            return 1
        elif x <= 0.07:
            return 1 - 0.5 * (x - 0.03) / 0.04
        else:
            return 0

    score = scoring_func(average_distance)
    return score

async def query_endpoint_for_iterator(
    endpoint: str, data: Dict[str, Any]
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(endpoint, json=data)
        return response


async def get_chat_data_validator_response(
    endpoint: str, data: Dict[str, Any]
) -> models.ValidatorCheckingResponse:
    """This method is fine as we always have max token is 1"""
    response = await query_endpoint_for_iterator(endpoint, data)
    async for line in response.aiter_lines():
        line_formatted = line.split("data: ")[1].split("\n\n")[0]
        response_json = json.loads(line_formatted)
        return models.ValidatorCheckingResponse(**response_json)


async def calculate_distance_for_token(
    task_config: models.TaskConfig,
    llm_request: models.ChatRequestModel,
    chat_responses: List[models.MinerChatResponse],
    index: int,
) -> float:
    validator_checking_response = await get_chat_data_validator_response(
        task_config.endpoint, llm_request.model_dump()
    )
    token = chat_responses[index].text
    validator_log_probs_for_token = {
        i.decoded: i.logprob for i in validator_checking_response.logprobs
    }

    if token not in validator_log_probs_for_token:
        return 1.0
    else:
        distance = abs(
            math.exp(validator_log_probs_for_token[token])
            - math.exp(chat_responses[index].logprob)
        )
    
    #formatted_validator_logging = "\n".join(
     #    [f"{i.decoded}: {i.logprob}" for i in validator_checking_response.logprobs]
     #)
    #logger.info(
     #    f"\nMiner token: {chat_responses[index].text}: {chat_responses[index].logprob} \n Validator tokens: \n{formatted_validator_logging}\ndistance between exp of log probs: {distance}"
     #)
    return distance