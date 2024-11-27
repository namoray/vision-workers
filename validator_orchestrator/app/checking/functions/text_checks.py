from typing import Dict, List, Set, Any, Optional, Union
from dataclasses import dataclass
from loguru import logger
import httpx
from app.core.constants import AI_SERVER_PORT
from transformers import AutoTokenizer


@dataclass
class LogProbObject:
    """Data class for token probability information"""
    logprob: float
    decoded_token: str


@dataclass
class TokenCheckResult:
    """Data class for token validation results"""
    is_valid: bool
    message: str
    token_index: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


async def check_response(
    prompt: str,
    response: List[str],
    tokenizer: AutoTokenizer,
    max_model_len: int,
    seed: int,
    max_tokens: int = 500,
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 5,
    logprobs: int = 10,
    logger_threshold: float = -10000  # don't think we need this with the rank check
) -> TokenCheckResult:
    try:
        prompt_token_ids = tokenizer(prompt)["input_ids"]

        total_tokens = len(prompt_token_ids) + len(response)
        logger.info(
            f"Total tokens: {total_tokens} ; prompt tokens: {len(prompt_token_ids)} ; response tokens: {len(response)}")

        prompt_data = await get_prompt_logprobs(
            prompt=prompt,
            response=response,
            temperature=temperature,
            seed=seed,
            top_p=top_p,
            top_k=top_k,
            logprobs=logprobs,
            max_tokens=1,
        )
        if not prompt_data or 'choices' not in prompt_data or not prompt_data['choices']:
            return TokenCheckResult(
                is_valid=False,
                message="Failed to get completions data"
            )

        first_choice = prompt_data['choices'][0]
        prompt_logprobs = first_choice.get('prompt_logprobs', {})

        for i, token in enumerate(response):
            current_prompt_logprobs = prompt_logprobs[i]
            rank_to_be_smaller_than = max(
                (logprob_obj['rank'] for logprob_obj in current_prompt_logprobs.values()
                 if logprob_obj.get('logprob', float('-inf')) > -float('inf')),
                default=1
            )

            if rank_to_be_smaller_than == logprobs:
                rank_to_be_smaller_than -= 1
            token_found = False
            for token_info in current_prompt_logprobs.values():
                if token_info.get('token') == token:
                    token_found = True
                    if token_info.get('rank', float('inf')) > rank_to_be_smaller_than:
                        logger.warning(
                            f"BAD index {i}! Token '{token}' has rank {token_info.get('rank')} vs threshold {rank_to_be_smaller_than}")
                        return TokenCheckResult(
                            is_valid=False,
                            token_index=i,
                            message=f"Invalid token '{token}' at position {i}"
                        )
                    break

            if not token_found:
                return TokenCheckResult(
                    is_valid=False,
                    message=f"Token '{token}' not found in logprobs at position {i}",
                    token_index=i,
                )

        # length validation
        if len(response) > max_tokens:
            return TokenCheckResult(
                is_valid=False,
                message=f"Response exceeds maximum length: {len(response)} > {max_tokens}"
            )

        logger.info("Length validation ✅")
        # EOT validation
        if len(response) < max_tokens:
            eot_data = await get_prompt_logprobs(
                prompt=prompt,
                response=response[:-1],
                temperature=temperature,
                seed=seed,
                top_p=top_p,
                top_k=top_k,
                logprobs=logprobs,
                max_tokens=1
            )
            if eot_data and 'choices' in eot_data and eot_data['choices']:
                first_eot_choice = eot_data['choices'][0]
                if 'logprobs' in first_eot_choice:
                    token_ids = [elm['index']
                                 for elm in first_eot_choice['logprobs']]
                    if tokenizer.eos_token_id not in token_ids:
                        # in case of finish reason = length
                        if len(response) != max_tokens and (max_model_len > len(prompt_token_ids) + len(response)):
                            return TokenCheckResult(
                                is_valid=False,
                                message=f"End-of-text token {tokenizer.eos_token_id} not in predicted tokens {token_ids}"
                            )

        logger.info("EOT validation ✅")
        return TokenCheckResult(
            is_valid=True,
            message="Response passed all validation checks"
        )

    except Exception as e:
        logger.error(f"Unexpected error in check_response: {str(e)}")
        logger.exception(e)
        return TokenCheckResult(
            is_valid=False,
            message=f"Validation failed due to error: {str(e)}"
        )


async def get_prompt_logprobs(
    prompt: str,
    response: List[str],
    temperature: float,
    seed: int,
    top_p: float = 0.95,
    top_k: int = 5,
    logprobs: int = 10,
    max_tokens: int = 100,
    server_name: str = "llm_server"
) -> Dict[str, Any]:

    full_text = prompt + ''.join(response)
    query_data = {
        "prompt": full_text,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "top_k": top_k,
        "prompt_logprobs": logprobs,
        "logprobs": logprobs,
        "seed": seed
    }
    try:
        response = await _query_completions(query_data, server_name)
        return response.json()

    except Exception as e:
        logger.error(f"Error getting completions data: {str(e)}")
        return {}


async def _query_completions(
    data: Dict[str, Any],
    server_name: str = "llm_server",
    timeout: int = 15
) -> httpx.Response:

    url = f"http://{server_name}:{AI_SERVER_PORT}/vali-completions"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Querying completion endpoint: {url}")
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response

    except httpx.TimeoutException:
        logger.error(f"Timeout querying completions endpoint after {timeout}s")
        raise
    except httpx.RequestError as e:
        logger.error(f"Network error querying completions endpoint: {str(e)}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error {e.response.status_code} from completions endpoint: {str(e)}")
        raise


def extract_token_info(
    token_data: Union[Dict[str, Any], LogProbObject]
) -> tuple[float, str]:
    if isinstance(token_data, dict):
        return (
            token_data.get('logprob', float('-inf')),
            token_data.get('decoded_token', '')
        )
    return (
        token_data.logprob,
        token_data.decoded_token
    )
