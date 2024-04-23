from typing import AsyncGenerator, List


from vllm import SamplingParams
from vllm.model_executor.utils import set_random_seed
from app import models
from app.models import Message, Role
import json
from app.logging import logging
from typing import Any

SYSTEM_PROMPT_PREFIX = "Instructions to follow for all following messages: "


def missing_system_prompts(tokenizer: Any) -> bool:
    return "must alternate" in tokenizer.chat_template.lower()


def _join_sequential_messages(
    current_content: str, new_content: str, add_system_instruction: bool = False
) -> str:
    # if there is already content, add a newline before adding the new content
    # otherwise, just add the new content
    return (
        f"{current_content}\n{new_content}" if len(current_content) > 0 else new_content
    )


def fix_message_structure_for_prompt(
    tokenizer: Any, messages: List[Message]
) -> List[Message]:
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
            processed_messages.append(
                Message(role=Role.assistant, content=assistant_buffer)
            )
            assistant_buffer = ""

    def _add_user_buffer_to_processed_messages() -> None:
        nonlocal user_message_buffer

        if user_message_buffer:
            processed_messages.append(
                Message(role=Role.user, content=user_message_buffer)
            )
            user_message_buffer = ""

    last_message_was_assistant: bool = False

    for message in messages:
        if message.role == Role.system:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            if len(user_message_buffer) == 0:
                user_message_buffer += SYSTEM_PROMPT_PREFIX

            user_message_buffer = _join_sequential_messages(
                user_message_buffer, message.content
            )
            last_message_was_assistant = False

        elif message.role == Role.user:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            user_message_buffer = _join_sequential_messages(
                user_message_buffer, message.content
            )
            last_message_was_assistant = False

        elif message.role == Role.assistant:
            if not last_message_was_assistant:
                _add_user_buffer_to_processed_messages()

            assistant_buffer = _join_sequential_messages(
                assistant_buffer, message.content
            )

            last_message_was_assistant = True

    if assistant_buffer:
        _add_assistant_buffer_to_processed_messages()
    elif user_message_buffer:
        _add_user_buffer_to_processed_messages()

    logging.debug(f"Processed messages: {processed_messages}")
    return processed_messages


async def complete_vllm(
    engine: models.LLMEngine, request_info: models.RequestInfo
) -> AsyncGenerator[str, None]:
    import uuid

    temperature = request_info.temperature

    seed = request_info.seed
    number_of_logprobs = request_info.number_of_logprobs
    starting_assistant_message = request_info.starting_assistant_message
    top_k = 5  # 5 is the maximum that vllm allows for logprobs, so we must use this
    top_p = request_info.top_p

    # Our use cases have top p 0 or 1
    if not top_p != 0:
        top_p = 1

    messages_dict = [
        message.model_dump()
        for message in fix_message_structure_for_prompt(
            engine.tokenizer, request_info.messages
        )
    ]
    # TODO: Review why system prompt doesn't work :(
    formatted_prompt = engine.tokenizer.apply_chat_template(
        conversation=messages_dict,
        tokenize=False,
        add_generation_prompt=starting_assistant_message)
    if 'llama-3' in engine.model_name and not starting_assistant_message:
        # we want to revmoe anything from the last instance of <|eot_id|> onwards
        formatted_prompt = formatted_prompt[:formatted_prompt.rfind("<|eot_id|>")]

    end_of_string_token = engine.tokenizer.eos_token
    if not starting_assistant_message and formatted_prompt.rstrip().endswith(
        end_of_string_token
    ):
        formatted_prompt = formatted_prompt.rstrip()[: -len(end_of_string_token)]

    set_random_seed(seed)
    sampling_params = SamplingParams(
        max_tokens=request_info.max_tokens,
        temperature=temperature,
        top_p=top_p,
        seed=seed,
        logprobs=number_of_logprobs,
        top_k=top_k,
    )
    stream = await engine.model.add_request(
        uuid.uuid4().hex, formatted_prompt, sampling_params
    )

    cursor = 0
    logprobs_cursor = 0
    async for request_output in stream:
        text = request_output.outputs[0].text
        latest_chunk = text[cursor:]

        log_probs = request_output.outputs[0].logprobs
        log_probs_dict = [
            {
                "index": idx,
                "logprob": token_detail.logprob,
                "decoded": token_detail.decoded_token,
            }
            for token_details in log_probs[logprobs_cursor:]
            for idx, token_detail in token_details.items()
        ]
        data = json.dumps(
            {"text": latest_chunk, "logprobs": log_probs_dict[:number_of_logprobs]}
        )
        yield f"data: {data}\n\n"

        cursor = len(text)
        logprobs_cursor = len(log_probs)
    yield "data: [DONE]\n\n"
