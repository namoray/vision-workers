from app.core import models
from typing import Dict, Any, List, Union
import httpx
import json
import random
import math
from loguru import logger
from app.core.constants import AI_SERVER_PORT

########### TEXT ###########


def _score_average_distance(average_distance: float, repeating_patterns_flag: bool) -> float:
    if repeating_patterns_flag:
        # If found repeating patterns, then be super harsh please
        return float(average_distance <= 0.05)
    elif average_distance <= 0.06:
        return 1
    elif average_distance <= 0.12:
        return 1 - 0.5 * (average_distance - 0.06) / 0.06
    else:
        return 0.0


async def _query_endpoint_for_iterator(endpoint: str, data: Dict[str, Any], server_name: str = "llm_server") -> httpx.Response:
    # TODO: Add ability to use localhost as the server name if set in env vars or similar
    url = f"http://{server_name}:{AI_SERVER_PORT}" + "/" + endpoint.lstrip("/")
    async with httpx.AsyncClient(timeout=5) as client:
        logger.info(f"Querying : {url}")
        response = await client.post(url, json=data)
        return response


async def _get_chat_data_validator_response(endpoint: str, data: Dict[str, Any], server_name: str = "llm_server") -> models.ValidatorCheckingResponse:
    """This method is fine as we always have max token is 1"""
    response = await _query_endpoint_for_iterator(endpoint, data, server_name)
    async for line in response.aiter_lines():
        line_formatted = line.split("data: ")[1].split("\n\n")[0]
        response_json = json.loads(line_formatted)
        return models.ValidatorCheckingResponse(**response_json)


async def _calculate_distance_for_token(
    task_config: models.OrchestratorServerConfig,
    llm_request: models.ChatRequestModel,
    chat_responses: List[models.Message],
    index: int,
    repeating_patterns_flag: bool = False,
) -> float:
    validator_checking_response = await _get_chat_data_validator_response(task_config.endpoint, llm_request.model_dump(), server_name=task_config.server_needed.value)
    token = chat_responses[index].content
    validator_log_probs_for_token = {i.decoded: i.logprob for i in validator_checking_response.logprobs}

    if token not in validator_log_probs_for_token:
        repeating_penalty = 10 if repeating_patterns_flag else 1
        return 1 * repeating_penalty
    else:
        distance = abs(math.exp(validator_log_probs_for_token[token]) - math.exp(chat_responses[index].logprob))

    return distance


min_occurences = {1: 4, 2: 3, 3: 3, 4: 3}


def _find_repeating_patterns(tokens: list[str]) -> dict[tuple[str, ...], tuple[int, int, int]]:
    n = len(tokens)
    patterns = {}

    start = 0
    while start < n:
        # Try each pattern length
        for length in range(1, (n - start) // 2 + 1):
            pattern = tuple(tokens[start : start + length])
            repeats = 1

            # Check how many times it repeats consecutively
            current_pos = start + length
            while current_pos + length <= n:
                if tuple(tokens[current_pos : current_pos + length]) == pattern:
                    repeats += 1
                    current_pos += length
                else:
                    break

            if repeats >= min_occurences.get(length, 2):
                patterns[pattern] = (repeats, length, start)
                start = current_pos - 1  # Skip to end of pattern
                break
        start += 1

    return patterns


async def check_text_result(result: models.QueryResult, payload: dict, task_config: models.OrchestratorServerConfig) -> Union[float, None]:
    repeating_patterns_flag = False

    formatted_response = json.loads(result.formatted_response) if isinstance(result.formatted_response, str) else result.formatted_response
    messages: list[models.MessageResponse] = []
    for response in formatted_response:
        try:
            content = response["choices"][0]["delta"]["content"]
            logprob = response["choices"][0]["logprobs"]["content"][0]["logprob"]
        except Exception as e:
            logger.error(f"Error with logprob: {e}. Response: {response}")
            return 0
        messages.append(models.MessageResponse(role="assistant", content=content, logprob=logprob))

    # If no responses, then not a good response
    if len(messages) == 0:
        return 0

    # Check to see if there are any repeating patterns

    if len(messages) == 1:
        indicies_to_check = [0]
    elif len(repeating_patterns := _find_repeating_patterns(messages)) > 0:
        repeating_patterns_flag = True
        for pattern, (count, length, pos) in repeating_patterns.items():
            logger.info(f"Found repeating pattern: {pattern} repeating {count} times at position {pos} with length {length}")

            # Always check first & last

            indicies_to_check = [0, len(messages) - 1]
            # Check first few occurences
            indicies_to_check.extend([pos, pos + 1, pos + 2, pos + 3])  # Check the start of the pattern

            # Check a few after the pattern
            indicies_to_check.append(pos + length)
            indicies_to_check.append(pos + length + 1)

            # Check one after the second pattern
            indicies_to_check.append(pos + length * 2)

            # Remove duplicates
            indicies_to_check = list(set(indicies_to_check))
    else:
        # Always check first & last
        indicies_to_check = [0, len(messages) - 1]
        number_of_additional_indicies_to_check = len(messages) - 2
        additional_indicies_to_check = random.sample(
            range(1, len(messages) - 1),
            number_of_additional_indicies_to_check,
        )
        indicies_to_check.extend(additional_indicies_to_check)

    total_distance = 0
    checks = 0

    payload["starting_assistant_message"] = True
    payload["number_of_logprobs"] = 5
    payload["top_k"] = 5

    llm_request = models.ChatRequestModel(**payload)
    llm_request.max_tokens = 1

    for index in indicies_to_check:
        if checks >= 5:
            continue

        if index == 0:
            llm_request.starting_assistant_message = True
        else:
            llm_request.starting_assistant_message = False

            text_to_inject_into_assistant_message = "".join([i.content for i in messages[:index]])
            llm_request.messages.append(
                models.Message(
                    **{
                        "role": "assistant",
                        "content": text_to_inject_into_assistant_message,
                    }
                )
            )

        distance = await _calculate_distance_for_token(task_config, llm_request, messages, index, repeating_patterns_flag)
        checks += 1
        # If repeating patterns, then be super harsh to make sure nothing went wrong
        total_distance += distance
        if index != 0:
            llm_request.messages = llm_request.messages[:-1]

    try:
        average_distance = total_distance / checks
    except Exception as e:
        logger.error(f"Error with average distance: {e}. Total distance: {total_distance}. Checks: {checks}")
        return 0
    score = _score_average_distance(average_distance, repeating_patterns_flag)
    return score
