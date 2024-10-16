import numpy as np
from typing import AsyncGenerator, List, Any
import imagehash
from PIL import Image
import httpx
import re
from loguru import logger
from app.core import utility_models
import io
import base64


def _hash_distance(hash_1: str, hash_2: str, color_hash: bool = False) -> int:
    if color_hash:
        restored_hash1 = imagehash.hex_to_flathash(hash_1, hashsize=3)
        restored_hash2 = imagehash.hex_to_flathash(hash_2, hashsize=3)
    else:
        restored_hash1 = imagehash.hex_to_hash(hash_1)
        restored_hash2 = imagehash.hex_to_hash(hash_2)

    return restored_hash1 - restored_hash2


def get_clip_embedding_similarity(clip_embedding1: List[float], clip_embedding2: List[float]):
    image_embedding1 = np.array(clip_embedding1, dtype=float).flatten()
    image_embedding2 = np.array(clip_embedding2, dtype=float).flatten()

    norm1 = np.linalg.norm(image_embedding1)
    norm2 = np.linalg.norm(image_embedding2)

    if norm1 == 0 or norm2 == 0:
        return float(norm1 == norm2)

    dot_product = np.dot(image_embedding1, image_embedding2)
    normalized_dot_product = dot_product / (norm1 * norm2)

    return float(normalized_dot_product)


def image_hash_feature_extraction(image: Image.Image) -> utility_models.ImageHashes:
    phash = str(imagehash.phash(image))
    ahash = str(imagehash.average_hash(image))
    dhash = str(imagehash.dhash(image))
    chash = str(imagehash.colorhash(image))

    return utility_models.ImageHashes(
        perceptual_hash=phash,
        average_hash=ahash,
        difference_hash=dhash,
        color_hash=chash,
    )


def pil_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def get_hash_distances(hashes_1: utility_models.ImageHashes, hashes_2: utility_models.ImageHashes) -> List[int]:
    ahash_distance = _hash_distance(hashes_1.average_hash, hashes_2.average_hash)
    phash_distance = _hash_distance(hashes_1.perceptual_hash, hashes_2.perceptual_hash)
    dhash_distance = _hash_distance(hashes_1.difference_hash, hashes_2.difference_hash)
    chash_distance = _hash_distance(hashes_1.color_hash, hashes_2.color_hash, color_hash=True)

    return [phash_distance, ahash_distance, dhash_distance, chash_distance]


def validate_gojourney_url(url: str) -> bool:
    if not url:
        return False
    pattern = re.compile(r"^https:\/\/img\.midjourneyapi\.xyz\/mj\/.*\.png$")
    if pattern.match(url):
        return True
    return False


async def fetch_image_as_bytes(url):
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.get(url)
            return response.content
    except Exception as e:
        logger.debug(f"Error when fetching image {url}: {e}")
        return False


SYSTEM_PROMPT_PREFIX = "Instructions to follow for all following messages: "


def missing_system_prompts(tokenizer: Any) -> bool:
    return "must alternate" in tokenizer.chat_template.lower()


def _join_sequential_messages(current_content: str, new_content: str, add_system_instruction: bool = False) -> str:
    # if there is already content, add a newline before adding the new content
    # otherwise, just add the new content
    return f"{current_content}\n{new_content}" if len(current_content) > 0 else new_content


def fix_message_structure_for_prompt(tokenizer: Any, messages: List[utility_models.Message]) -> List[utility_models.Message]:
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
            processed_messages.append(utility_models.Message(role=utility_models.Role.user, content=":"))

        if assistant_buffer:
            processed_messages.append(utility_models.Message(role=utility_models.Role.assistant, content=assistant_buffer))
            assistant_buffer = ""

    def _add_user_buffer_to_processed_messages() -> None:
        nonlocal user_message_buffer

        if user_message_buffer:
            processed_messages.append(utility_models.Message(role=utility_models.Role.user, content=user_message_buffer))
            user_message_buffer = ""

    last_message_was_assistant: bool = False

    for message in messages:
        if message.role == utility_models.Role.system:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            if len(user_message_buffer) == 0:
                user_message_buffer += SYSTEM_PROMPT_PREFIX

            user_message_buffer = _join_sequential_messages(user_message_buffer, message.content)
            last_message_was_assistant = False

        elif message.role == utility_models.Role.user:
            if last_message_was_assistant:
                _add_assistant_buffer_to_processed_messages()

            user_message_buffer = _join_sequential_messages(user_message_buffer, message.content)
            last_message_was_assistant = False

        elif message.role == utility_models.Role.assistant:
            if not last_message_was_assistant:
                _add_user_buffer_to_processed_messages()

            assistant_buffer = _join_sequential_messages(assistant_buffer, message.content)

            last_message_was_assistant = True

    if assistant_buffer:
        _add_assistant_buffer_to_processed_messages()
    elif user_message_buffer:
        _add_user_buffer_to_processed_messages()

    logger.debug(f"Processed messages: {processed_messages}")
    return processed_messages