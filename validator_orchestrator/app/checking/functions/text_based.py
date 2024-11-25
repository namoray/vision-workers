from typing import Dict, List, Any, Union, Optional
import httpx
import json
import random
from transformers import AutoTokenizer
import math
from loguru import logger

from app.core import models
from app.core.constants import AI_SERVER_PORT
from app.checking.functions.text_checks import check_response

tokenizer_name = "tau-vision/llama-tokenizer-fix"
tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

BOTTOM_TEXT_THRESHOLD = 0.125
TOP_TEXT_THRESHOLD = 0.25

def _score_average_distance(average_distance: float, alpha: int = 5) -> float:
    """
    Calculate quality score from logprobs average distances.
    
    Args:
        average_distance: Average distance between expected and actual logprobs
        alpha: Severity factor for penalizing large distances
    
    Returns:
        float: Normalized score between 0 and 1
    """
    if average_distance <= BOTTOM_TEXT_THRESHOLD:
        return 1.0
    elif average_distance <= TOP_TEXT_THRESHOLD:
        return 1.0 - 0.5 * (average_distance - BOTTOM_TEXT_THRESHOLD) / (TOP_TEXT_THRESHOLD - BOTTOM_TEXT_THRESHOLD)
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
) -> float:
    validator_checking_response = await _get_chat_data_validator_response(task_config.endpoint, llm_request.model_dump(), server_name=task_config.server_needed.value)
    token = chat_responses[index].content
    validator_log_probs_for_token = {i.decoded: i.logprob for i in validator_checking_response.logprobs}
    logger.info(f"token : {token} - logprob : {chat_responses[index].logprob}")
    logger.info(f"validator_log_probs_for_token : {validator_log_probs_for_token}")
    if token not in validator_log_probs_for_token:
        return 1.0
    else:
        distance = abs(math.exp(validator_log_probs_for_token[token]) - math.exp(chat_responses[index].logprob))

    return distance

def chat_to_prompt(
    messages: List[Dict[str, str]],
    model_name: str,
    starting_assistant_message: bool = True
) -> str:
    global tokenizer

    formatted_prompt = tokenizer.apply_chat_template(
        conversation=messages,
        tokenize=False,
        add_generation_prompt=starting_assistant_message
    )
    
    if "llama-3" in model_name.lower() and not starting_assistant_message:
        formatted_prompt = formatted_prompt[: formatted_prompt.rfind("<|eot_id|>")]
        
    end_of_string_token = tokenizer.eos_token
    if not starting_assistant_message and formatted_prompt.rstrip().endswith(end_of_string_token):
        formatted_prompt = formatted_prompt.rstrip()[: -len(end_of_string_token)]
        
    return formatted_prompt

async def check_text_result(
    result: models.QueryResult,
    payload: dict,
    task_config: models.OrchestratorServerConfig
) -> Union[float, None]:
    global tokenizer, tokenizer_name

    if task_config.load_model_config['tokenizer'] != tokenizer_name:
        tokenizer = AutoTokenizer.from_pretrained(task_config.load_model_config['tokenizer'])
        tokenizer_name = task_config.load_model_config['tokenizer']

    try:
        # Parse formatted response
        formatted_response = (
            json.loads(result.formatted_response)
            if isinstance(result.formatted_response, str)
            else result.formatted_response
        )
        
        # Extract messages and validate format
        messages: List[models.MessageResponse] = []
        response_tokens: List[str] = []
        for response in formatted_response:
            try:
                content = response["choices"][0]["delta"]["content"]
                logprobs = response["choices"][0]["logprobs"]
                # Below is a fix for the first message not having logprobs
                if content == "" and logprobs is None:
                    role = response["choices"][0]["delta"]["role"]
                    if role == "assistant":
                        continue
                logprob = logprobs["content"][0]["logprob"]
                messages.append(models.MessageResponse(role="assistant", content=content, logprob=logprob))
            except Exception as e:
                logger.error(f"Error with logprob: {e}. Response: {response}")
                logger.exception(e)
                return 0  # Important to return 0 as this is a critical error
            
        if not messages:
            logger.warning("No valid messages in response")
            return 0.0
        
        response_tokens = [elm.content for elm in messages]
        prompt = chat_to_prompt(payload["messages"], task_config.task)
        
        # Validate response tokens
        if tokenizer and response_tokens:
            logger.info("Validating response tokens")
            validation_result = await check_response(
                prompt=prompt,
                response=response_tokens,
                tokenizer=tokenizer,
                max_model_len=task_config.load_model_config['max_model_len'],
                max_tokens=payload.get("max_tokens", 500),
                temperature=payload.get("temperature", 0.5),
                top_p=payload.get("top_p", 0.95),
                seed=payload.get("seed", 369)
            )
            
            if not validation_result.is_valid:
                logger.warning(f"Response validation failed: {validation_result.message}")
                return 0.0
        
        if messages[-1].content == "":
            messages = messages[:-1]

        if len(messages) == 1:
            indicies_to_check = [0]
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
            distance = await _calculate_distance_for_token(task_config, llm_request, messages, index)
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
        
    except Exception as e:
        logger.error(f"Critical error in check_text_result: {str(e)}")
        logger.exception(e)
        return None