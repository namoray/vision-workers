from app.core import models
from typing import Dict, Any, List, Union
import httpx
import json
import random
import math
from loguru import logger
from app.core.constants import AI_SERVER_PORT
from app.checking.utils import fix_message_structure_for_prompt
from transformers import AutoTokenizer


########### TEXT ###########

BOTTOM_TEXT_THRESHOLD = 0.125
TOP_TEXT_THRESHOLD = 0.25


def _score_average_distance(average_distance: float, alpha: int = 5) -> float:
    """Calculate quality score from logprobs average distances.
    alpha decides how severe we penalize for big distances"""
    if average_distance <= BOTTOM_TEXT_THRESHOLD:
        return 1
    elif average_distance <= TOP_TEXT_THRESHOLD:
        return 1 - 0.5 * (average_distance - BOTTOM_TEXT_THRESHOLD) / (TOP_TEXT_THRESHOLD - BOTTOM_TEXT_THRESHOLD)
    else:
        return 0


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
) -> tuple[float, str]:
    validator_checking_response = await _get_chat_data_validator_response(task_config.endpoint, llm_request.model_dump(), server_name=task_config.server_needed.value)
    token = chat_responses[index].content
    validator_log_probs_for_token = {i.decoded: i.logprob for i in validator_checking_response.logprobs}

    if token not in validator_log_probs_for_token:
        return 1.0, validator_checking_response.finish_reason
    else:
        distance = abs(math.exp(validator_log_probs_for_token[token]) - math.exp(chat_responses[index].logprob))

    return distance, validator_checking_response.finish_reason


async def check_text_result(result: models.QueryResult, payload: dict, task_config: models.OrchestratorServerConfig) -> Union[float, None]:
    formatted_response = json.loads(result.formatted_response) if isinstance(result.formatted_response, str) else result.formatted_response
    messages: list[models.MessageResponse] = []
    last_response = None
    for response in formatted_response:
        try:
            content = response["choices"][0]["delta"]["content"]
            logprobs = response["choices"][0]["logprobs"]
            # Below is a fix for the first message not having logprobs
            if content == "" and logprobs is None:
                role = response["choices"][0]["delta"]["role"]
                if role == "assistant":
                    continue
            if response["choices"][0]["finish_reason"]:
                last_response = response
            
            logprob = logprobs["content"][0]["logprob"]
            messages.append(models.MessageResponse(role="assistant", content=content, logprob=logprob))
        except Exception as e:
            logger.error(f"Error with logprob: {e}. Response: {response}")
            return 0  # Important to return 0 as this is a critical error

    try:
        assert last_response is not None
    except AssertionError as e:
        logger.error(f"Error with last response: {e}; miner's last response taken doesn't have finish reason ; Response: {last_response}")
        return 0

    tokenizer = AutoTokenizer.from_pretrained(task_config.load_model_config["tokenizer"])
    logger.info(f"[DEBUGG]: payload['messages']: {payload['messages']}")
    messages_dict = [message for message in fix_message_structure_for_prompt(tokenizer, payload["messages"])]
    # messages_dict = payload["messages"]
    logger.info(f"[DEBUGG]: messages_dict: {messages_dict}")
    input_prompt_tokens = tokenizer.apply_chat_template(conversation=messages_dict, tokenize=True, add_generation_prompt=payload["starting_assistant_message"])
    num_input_prompt_tokens = len(input_prompt_tokens)

    num_output_prompt_tokens = len(messages)

    # Model tried to output more tokens than are possible? you cannae do that
    try:
        assert num_input_prompt_tokens + num_output_prompt_tokens <= task_config.load_model_config["max_model_len"]
    except AssertionError as e:
        logger.error(f"Miner generated more than max model length?!: {e}")
        return 0
    
    logger.info(f"num_input_prompt_tokens: {num_input_prompt_tokens} ; num_output_prompt_tokens: {num_output_prompt_tokens}")
    if last_response["choices"][0]["finish_reason"] == "length":
        try:
            assert num_input_prompt_tokens + num_output_prompt_tokens == task_config.load_model_config["max_model_len"] or num_output_prompt_tokens == payload["max_tokens"]
        except AssertionError as e:
            logger.error(f"Finish reason = 'length' but neither (i) miner generation + input tokens equal to max model length or (ii) output tokens equal to max tokens; Error trace: {e}")
            return 0
    elif last_response["choices"][0]["finish_reason"] == "stop":
        #We check this thoroughly afterwards
        pass    
    

    # If no responses, then not a good response
    if len(messages) == 0:
        return 0

    if len(messages) == 1:
        indicies_to_check = [0]
    else:
        # Always check first & last
        indicies_to_check = [0]
        number_of_additional_indicies_to_check = len(messages) - 2
        additional_indicies_to_check = random.sample(
            range(1, len(messages) - 1),
            number_of_additional_indicies_to_check,
        )
        indicies_to_check.extend(additional_indicies_to_check)
        indicies_to_check.extend([len(messages) - 1])

    total_distance = 0
    checks = 0

    payload["starting_assistant_message"] = True
    payload["number_of_logprobs"] = 5
    payload["top_k"] = 5

    llm_request = models.ChatRequestModel(**payload)
    llm_request.max_tokens = 1

    for counter, index in enumerate(indicies_to_check):
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
        distance, finish_reason = await _calculate_distance_for_token(task_config, llm_request, messages, index)

        # Check that the last token generated by validator llm checking server agrees that the sequence has indeed ended
        if counter == len(indicies_to_check) - 1:
            # We already manually handled the finish_reason == "length" case above, but just to be sure
            try:
                assert finish_reason == "stop" or finish_reason == "length"
            except AssertionError as e:
                logger.error(f"Validator's LLM checking server's last token doesn't indicate the sequence has stopped generating!: {e}")
                return 0
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
