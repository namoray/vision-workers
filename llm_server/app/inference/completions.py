from typing import AsyncGenerator, List


from vllm import SamplingParams
from vllm.model_executor.utils import set_random_seed
from app import models
from app.models import Message, Role
import json
from app.logging import logging
from typing import Any
from loguru import logger
from typing import List, Any, Union


SYSTEM_PROMPT_PREFIX = "Instructions to follow for all following messages: "


def missing_system_prompts(tokenizer: Any) -> bool:
    return "must alternate" in tokenizer.chat_template.lower()


def _join_sequential_messages(current_content: str, new_content: str, add_system_instruction: bool = False) -> str:
    # if there is already content, add a newline before adding the new content
    # otherwise, just add the new content
    return f"{current_content}\n{new_content}" if len(current_content) > 0 else new_content


def fix_message_structure_for_prompt(tokenizer: Any, messages: List[Message]) -> List[Message]:
    """
    Because the chat_formats in the tokenizer are fixed and don't allow things like system instructions (mistralai),
    or message ordering like usr -> usr -> assistant we need to fix the message structure before sending it to the model
    we do this by joining the system prompt to the next user (or a blank user message) for mistral
    and joining usr -> usr to become usr:concat(usr, usr), ass -> ass to become ass:concat(ass, ass)
    If there is a system message with mistral we join it with the next usr message so sys -> sys -> usr becomes usr:concat(sys, sys, usr)
    """

    # Mistral can't handle system prompts. If Mistral is detected, we need to join the system prompt with the next user message
    if not missing_system_prompts(tokenizer):
        return messages

    user_message_buffer: str = ""
    assistant_buffer: str = ""
    processed_messages: List[str] = []

    def _add_assistant_buffer_to_processed_messages() -> None:
        nonlocal assistant_buffer

        # Edge case if assistant is the first messsage:
        if len(processed_messages) == 0:
            processed_messages.append(Message(role=Role.user, content=":"))

        if assistant_buffer:
            processed_messages.append(Message(role=Role.assistant, content=assistant_buffer))
            assistant_buffer = ""

    def _add_user_buffer_to_processed_messages() -> None:
        nonlocal user_message_buffer

        if user_message_buffer:
            processed_messages.append(Message(role=Role.user, content=user_message_buffer))
            user_message_buffer = ""

    last_message_was_assistant: bool = False

    for message in messages:
        if message.role == Role.system:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            if len(user_message_buffer) == 0:
                user_message_buffer += SYSTEM_PROMPT_PREFIX

            user_message_buffer = _join_sequential_messages(user_message_buffer, message.content)
            last_message_was_assistant = False

        elif message.role == Role.user:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            user_message_buffer = _join_sequential_messages(user_message_buffer, message.content)
            last_message_was_assistant = False

        elif message.role == Role.assistant:
            if not last_message_was_assistant:
                _add_user_buffer_to_processed_messages()

            assistant_buffer = _join_sequential_messages(assistant_buffer, message.content)

            last_message_was_assistant = True

    if assistant_buffer:
        _add_assistant_buffer_to_processed_messages()
    elif user_message_buffer:
        _add_user_buffer_to_processed_messages()

    logging.debug(f"Processed messages: {processed_messages}")
    return processed_messages


async def complete_vllm(engine: models.LLMEngine, 
                       request_info: models.RequestInfo,
) -> Union[AsyncGenerator[str, None], dict]:
    import uuid

    temperature = request_info.temperature
    stream = getattr(request_info, 'stream', True)
    seed = request_info.seed
    number_of_logprobs = request_info.number_of_logprobs
    prompt_logprobs = request_info.prompt_logprobs
    starting_assistant_message = request_info.starting_assistant_message
    top_k = 5  # 5 is the maximum that vllm allows for logprobs
    top_p = request_info.top_p if request_info.top_p in [0, 1] else 1

    if hasattr(request_info, 'prompt'):
        formatted_prompt = request_info.prompt
    else:
        messages_dict = [message.model_dump() for message in fix_message_structure_for_prompt(engine.tokenizer, request_info.messages)]
        formatted_prompt = engine.tokenizer.apply_chat_template(conversation=messages_dict, tokenize=False, add_generation_prompt=starting_assistant_message)
        if "llama-3" in engine.model_name.lower() and not starting_assistant_message:
            formatted_prompt = formatted_prompt[: formatted_prompt.rfind("<|eot_id|>")]

        end_of_string_token = engine.tokenizer.eos_token
        if not starting_assistant_message and formatted_prompt.rstrip().endswith(end_of_string_token):
            formatted_prompt = formatted_prompt.rstrip()[: -len(end_of_string_token)]

    set_random_seed(seed)

    if not stream:
        sampling_params = SamplingParams(
            max_tokens=request_info.max_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            logprobs=number_of_logprobs,
            top_k=top_k,
            prompt_logprobs=prompt_logprobs
        )
        request_output = await engine.model.add_request(uuid.uuid4().hex, formatted_prompt, sampling_params)

        logprobs_cursor = 0
        cursor = 0
        async for output in request_output:
            text = output.outputs[0].text
            log_probs = output.outputs[0].logprobs
            prompt_log_probs = output.prompt_logprobs
            
            logger.info(f"{output}")
            logger.info('-----'*5)

            formatted_prompt_logprobs = {}
            if prompt_log_probs:
                for i, token_logprobs in enumerate(prompt_log_probs):
                    if token_logprobs:
                        formatted_prompt_logprobs[str(i)] = {
                            str(token_id): {
                                "logprob": logprob.logprob,
                                "token": logprob.decoded_token,
                                "rank": logprob.rank
                            }
                            for token_id, logprob in token_logprobs.items()
                        }

            choices_data = {
                "choices": [{
                    "delta": {
                        "content": text
                    },
                    "logprobs": {
                        "content": [
                            {
                                "index": index,
                                "logprob": token_detail.logprob,
                                "token": token_detail.decoded_token
                            }
                            for token_details in log_probs
                            for index, token_detail in token_details.items()
                        ]
                    },
                    "prompt_logprobs": prompt_log_probs
                }]
            }
            
        yield f"data: {json.dumps(choices_data)}\n\n"
    else:
        sampling_params = SamplingParams(
            max_tokens=request_info.max_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            logprobs=number_of_logprobs,
            top_k=top_k
        )
        request_output = await engine.model.add_request(uuid.uuid4().hex, formatted_prompt, sampling_params)
        logprobs_cursor = 0
        cursor = 0
        async for output in request_output:
            text = output.outputs[0].text
            latest_chunk = text[cursor:]

            logger.info(f"text: {text}")
            logger.info('-----'*5)

            log_probs = output.outputs[0].logprobs
            log_probs_dict = [
                {
                    "index": idx,
                    "logprob": token_detail.logprob,
                    "decoded": token_detail.decoded_token,
                }
                for token_details in log_probs[logprobs_cursor:]
                for idx, token_detail in token_details.items()
            ]
            data = {"text": latest_chunk, "logprobs": log_probs_dict[:number_of_logprobs]}
            if data["text"] and data["logprobs"]:
                yield f"data: {json.dumps(data)}\n\n"

            cursor = len(text)
            logprobs_cursor = len(log_probs)
        yield "data: [DONE]\n\n"