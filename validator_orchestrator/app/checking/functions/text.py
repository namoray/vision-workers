from app.core import models
from typing import List, Union
import json
from loguru import logger
import httpx

PROMPT_KEY = "prompt"
MESSAGES_KEY = "messages"

# TODO: Change below to local docker container, and eventually to chutes
BASE_URL = "http://83.143.115.20:8000"


def _payload_is_completions(payload: dict) -> bool:
    return PROMPT_KEY in payload


def _extract_completions_message(idx: int, response: dict) -> str:
    content = response["choices"][0]["text"]
    logprobs = response["choices"][0]["logprobs"]

    # Sometimes the first message is empty and doesn't have logprobs, skip it
    if idx == 0 and content == "" and logprobs is None:
        return None

    logprob = logprobs["token_logprobs"][0]
    return models.MessageResponse(role="assistant", content=content, logprob=logprob)


def _extract_chat_message(idx: int, response: dict) -> models.MessageResponse | None:
    content = response["choices"][0]["delta"]["content"]
    logprobs = response["choices"][0]["logprobs"]
    # Below is a fix for the first message not having logprobs
    if idx == 0 and content == "" and logprobs is None:
        role = response["choices"][0]["delta"]["role"]
        if role == "assistant":
            return None
    logprob = logprobs["content"][0]["logprob"]
    return models.MessageResponse(role="assistant", content=content, logprob=logprob)


async def _tokenize(prompt: str, model: str = "unsloth/Meta-Llama-3.1-8B-Instruct") -> list[int]:
    async with httpx.AsyncClient() as client:
        r = await client.post(url=f"{BASE_URL}/tokenize", json={"model": model, "prompt": prompt})
        r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        return r.json()["tokens"]


async def _detokenize(tokens: list[int], model: str = "unsloth/Meta-Llama-3.1-8B-Instruct"):
    async with httpx.AsyncClient() as client:
        r = await client.post(url=f"{BASE_URL}/detokenize", json={"tokens": tokens, "model": model})
        r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        return r.json()["prompt"]


async def _tokenize_and_detokenize(input_payload: dict, model_name: str, eos_token_id: int = 128009, add_generation_prompt: bool = True) -> tuple[str, int]:
    async with httpx.AsyncClient() as http_client:
        tokenize_response = await http_client.post(url=f"{BASE_URL}/tokenize", json=input_payload)
        tokenize_response.raise_for_status()
        token_list: list[int] = tokenize_response.json()["tokens"]

        if "llama-3" in model_name.lower() and not add_generation_prompt:
            last_eot_index = max((index for index, value in enumerate(token_list) if value == eos_token_id), default=None)
            if last_eot_index is not None:
                token_list = token_list[:last_eot_index]

        detokenize_response = await http_client.post(url=f"{BASE_URL}/detokenize", json={"tokens": token_list, "model": model_name})
        detokenize_response.raise_for_status()

        prompt = detokenize_response.json()["prompt"]
        return prompt, len(token_list)


async def _chat_to_prompt(messages: list[dict], model_name: str, eos_token_id: int = 128009, add_generation_prompt: bool = True) -> tuple[str, int]:
    input_payload = {"model": model_name, "messages": messages}
    return await _tokenize_and_detokenize(input_payload, model_name, eos_token_id, add_generation_prompt)


async def _completions_to_prompt(prompt: str, model_name: str, eos_token_id: int = 128009, add_generation_prompt: bool = True) -> tuple[str, int]:
    input_payload = {"model": model_name, "prompt": prompt}
    return await _tokenize_and_detokenize(input_payload, model_name, eos_token_id, add_generation_prompt)


async def check_text_result(result: models.QueryResult, payload: dict, task_config: models.OrchestratorServerConfig) -> Union[float, None]:
    formatted_response = json.loads(result.formatted_response) if isinstance(result.formatted_response, str) else result.formatted_response
    eos_token_id = task_config.load_model_config["eos_token_id"]

    # Extract messages & logprobs from the response

    messages: List[models.MessageResponse] = []
    response_tokens: List[str] = []
    for idx, response in enumerate(formatted_response):
        try:
            # If `prompt` is in the payload, treat it as a /completions request
            if _payload_is_completions(payload):
                message = _extract_completions_message(idx, response)
            else:
                message = _extract_chat_message(idx, response)

            if message is not None:
                messages.append(message)
        except Exception as e:
            logger.error(f"Error with logprob: {e}. Response: {response}")
            logger.exception(e)
            return 0  # Important to return 0 as this is a critical error

    if not messages:
        logger.error("No valid messages in response.")
        logger.exception(formatted_response)
        return 0.0

    if len(messages) > payload["max_tokens"]:
        logger.error("Number of messages is greater than max_tokens, skipping logprob check, returning 0")
        return 0.0

    # Now get the combined input + output in `prompt` format
    if _payload_is_completions(payload):
        input_completions_content = payload[PROMPT_KEY]
        input_content, num_input_tokens = await _completions_to_prompt(input_completions_content, task_config.load_model_config["model"], eos_token_id, add_generation_prompt=False)
    else:
        input_chat_content = payload[MESSAGES_KEY]
        input_content, num_input_tokens = await _chat_to_prompt(input_chat_content, task_config.load_model_config["model"], eos_token_id, add_generation_prompt=False)

    full_response_content = "".join([message.content for message in messages])

    full_prompt_before_eos = input_content + full_response_content
    response_tokens = await _tokenize(full_prompt_before_eos, task_config.load_model_config["model"])

    # Make sure the last token is eos token where necessary, so we can check it with prompt logprobs
    number_of_output_tokens = len(messages)
    if number_of_output_tokens != payload["max_tokens"] and response_tokens[-1] != eos_token_id:
        response_tokens.append(eos_token_id)

    full_prompt = await _detokenize(response_tokens, task_config.load_model_config["model"])

    # Now get the prompt logprobs from completions and check they are all correct
    r = httpx.post(
        f"{BASE_URL}/v1/completions",
        json={
            "prompt": full_prompt,
            "model": task_config.load_model_config["model"],
            "temperature": 1.0,
            "max_tokens": 1,
            "prompt_logprobs": 2,
        },
    )

    result = json.loads(r.text)
    prompt_logprobs = result["choices"][0]["prompt_logprobs"][num_input_tokens:]

    print(prompt_logprobs)

    return 0.0
