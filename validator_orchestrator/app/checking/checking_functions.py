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

images_are_same_classifier = xgb.XGBClassifier()
images_are_same_classifier.load_model("image_similarity_xgb_model.json")

### CLIP  ####


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
    async with httpx.AsyncClient(timeout=45) as client:
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

    total_distance = 0
    checks = 0

    synapse["number_of_logprobs"] = 5
    synapse["starting_assistant_message"] = True
    llm_request = models.ChatRequestModel(**synapse)
    llm_request.max_tokens = 1

    # Check the first token, always
    distance = await calculate_distance_for_token(
        task_config, llm_request, miner_chat_responses, 0
    )
    total_distance += distance
    checks += 1

    if len(miner_chat_responses) >= 3:
        while checks < 10:
            # Pick random token that's not the first from the miner, construct the new validator
            # checking data, and check that
            index = random.randint(1, len(miner_chat_responses) - 2)
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
            total_distance += distance
            checks += 1

            llm_request.messages = llm_request.messages[:-1]

        average_distance = total_distance / checks

    score = 1 if average_distance <= 0.10 else 0.9 if average_distance <= 0.20 else 0
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
    response = await query_endpoint_for_iterator(endpoint, data)
    async for line in response.aiter_lines():
        response_json = json.loads(line.split("data: ")[1].split("\n\n")[0])
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
        distance = math.exp(chat_responses[index].logprob) + 1
        logger.debug(f"Token not in validator_log {token}")
    else:
        distance = abs(
            math.exp(validator_log_probs_for_token[token])
            - math.exp(chat_responses[index].logprob)
        )
        logger.debug(f"Distance between probs: {distance}")

    # formatted_validator_logging = "\n".join(
    #     [f"{i.decoded}: {i.logprob}" for i in validator_checking_response.logprobs]
    # )
    # logger.info(
    #     f"\nMiner token: {chat_responses[index].text}: {chat_responses[index].logprob} \n Validator tokens: \n{formatted_validator_logging}\ndistance between exp of log probs: {distance}"
    # )
    return int(distance >= 0.2)
