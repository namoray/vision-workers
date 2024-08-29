from app.core import models
from typing import Dict, Any, List, Union
import httpx
import json
import random
import math
from loguru import logger
from app.core.constants import AI_SERVER_PORT


########### TEXT ###########


def _score_average_distance(average_distance: float) -> float:
    if average_distance <= 0.06:
        return 1
    elif average_distance <= 0.12:
        return 1 - 0.5 * (average_distance - 0.06) / 0.06
    else:
        return 0.0


async def _query_endpoint_for_iterator(endpoint: str, data: Dict[str, Any]) -> httpx.Response:
    url = f"http://localhost:" + AI_SERVER_PORT + '/' + endpoint.lstrip('/')
    async with httpx.AsyncClient(timeout=5) as client:
        logger.info(f"Querying : {url}")
        response = await client.post(url, json=data)
        logger.info(response)
        return response


async def _get_chat_data_validator_response(endpoint: str, data: Dict[str, Any]) -> models.ValidatorCheckingResponse:
    """This method is fine as we always have max token is 1"""
    response = await _query_endpoint_for_iterator(endpoint, data)
    async for line in response.aiter_lines():
        line_formatted = line.split("data: ")[1].split("\n\n")[0]
        response_json = json.loads(line_formatted)
        return models.ValidatorCheckingResponse(**response_json)


async def _calculate_distance_for_token(
    task_config: models.OrchestratorServerConfig,
    llm_request: models.ChatRequestModel,
    chat_responses: List[models.MinerChatResponse],
    index: int,
) -> float:
    validator_checking_response = await _get_chat_data_validator_response(task_config.endpoint, llm_request.model_dump())
    token = chat_responses[index].text
    validator_log_probs_for_token = {i.decoded: i.logprob for i in validator_checking_response.logprobs}

    if token not in validator_log_probs_for_token:
        return 1.0
    else:
        distance = abs(math.exp(validator_log_probs_for_token[token]) - math.exp(chat_responses[index].logprob))

    return distance


async def check_text_result(result: models.QueryResult, synapse: Dict[str, Any], task_config: models.OrchestratorServerConfig) -> Union[float, None]:
    formatted_response = json.loads(result.formatted_response) if isinstance(result.formatted_response, str) else result.formatted_response
    miner_chat_responses: List[models.MinerChatResponse] = [models.MinerChatResponse(**r) for r in formatted_response]

    # If no responses, then not a good response
    if len(miner_chat_responses) == 0:
        return 0

    if len(miner_chat_responses) == 1:
        indicies_to_check = [0]
    else:
        # Always check first & last
        indicies_to_check = [0, len(miner_chat_responses) - 1]
        number_of_additional_indicies_to_check = len(miner_chat_responses) - 2
        additional_indicies_to_check = random.sample(
            range(1, len(miner_chat_responses) - 1),
            number_of_additional_indicies_to_check,
        )
        indicies_to_check.extend(additional_indicies_to_check)

    total_distance = 0
    checks = 0

    synapse["starting_assistant_message"] = True
    synapse["number_of_logprobs"] = 5
    synapse["top_k"] = 5

    llm_request = models.ChatRequestModel(**synapse)
    llm_request.max_tokens = 1

    for index in indicies_to_check:
        if checks >= 5:
            continue

        if index == 0:
            llm_request.starting_assistant_message = True
        else:
            llm_request.starting_assistant_message = False

            text_to_inject_into_assistant_message = "".join([i.text for i in miner_chat_responses[:index]])
            llm_request.messages.append(
                models.Message(
                    **{
                        "role": "assistant",
                        "content": text_to_inject_into_assistant_message,
                    }
                )
            )

        distance = await _calculate_distance_for_token(task_config, llm_request, miner_chat_responses, index)
        checks += 1
        total_distance += distance
        if index != 0:
            llm_request.messages = llm_request.messages[:-1]

    try:
        average_distance = total_distance / checks
    except Exception as e:
        logger.error(f"Error with average distance: {e}. Total distance: {total_distance}. Checks: {checks}")
        return 0
    score = _score_average_distance(average_distance)
    return score