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
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 5,
    logprobs: int = 20,
    max_tokens: int = 1000,
    logger_threshold: float = -10000,
) -> TokenCheckResult:
    try:
        prompt_token_ids = tokenizer(prompt)["input_ids"]
        
        prompt_loggers = await get_prompt_logprobs(
            prompt=prompt,
            response=response,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            logprobs=logprobs
        )
        
        if not prompt_loggers:
            return TokenCheckResult(
                is_valid=False,
                message="Failed to get prompt logprobs"
            )
        
        response_loggers = prompt_loggers[len(prompt_token_ids):]
        
        for i, (token, token_logprobs) in enumerate(zip(response, response_loggers)):
            allowed_tokens: Set[str] = set()
            
            for token_id, logprob_data in token_logprobs.items():
                if isinstance(logprob_data, dict):
                    token_logprob = logprob_data.get('logprob', float('-inf'))
                    token_text = logprob_data.get('decoded_token', '')
                else:
                    token_logprob = getattr(logprob_data, 'logprob', float('-inf'))
                    token_text = getattr(logprob_data, 'decoded_token', '')
                
                if token_logprob > logger_threshold:
                    allowed_tokens.add(token_text)
            
            if token not in allowed_tokens:
                return TokenCheckResult(
                    is_valid=False,
                    message=f"Invalid token at position {i}",
                    token_index=i,
                    details={
                        'token': token,
                        'allowed_tokens': list(allowed_tokens)
                    }
                )
        logger.info("Allowed tokens validation ✅")

        # length validation
        if len(response) > max_tokens:
            return TokenCheckResult(
                is_valid=False,
                message=f"Response exceeds maximum length: {len(response)} > {max_tokens}"
            )
        logger.info("Length validation ✅")
        
        # EOT validation
        if len(response) < max_tokens:
            eos_logprobs = await get_prompt_logprobs(
                prompt=prompt + ''.join(response),
                response=[],
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                logprobs=logprobs
            )
            
            if eos_logprobs:
                first_token_logprobs = eos_logprobs[0]
                if not any(tokenizer.eos_token_id == int(token_id) 
                          for token_id in first_token_logprobs.keys()):
                    return TokenCheckResult(
                        is_valid=False,
                        message="End-of-text token not found in likely next tokens"
                    )
        logger.info("Length validation ✅")
        return TokenCheckResult(
            is_valid=True,
            message="Response passed all validation checks"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in check_response: {str(e)}")
        return TokenCheckResult(
            is_valid=False,
            message=f"Validation failed due to error: {str(e)}"
        )
    
async def get_prompt_logprobs(
    prompt: str,
    response: List[str],
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 5,
    logprobs: int = 20,
    server_name: str = "llm_server"
) -> List[Dict[str, Any]]:
    
    full_text = prompt + ''.join(response)
    query_data = {
        "prompt": full_text,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 1,
        "top_k": top_k,
        "prompt_logprobs": logprobs,
        "logprobs": logprobs
    }
    
    try:
        response = await _query_completions(query_data, server_name)
        response_data = response.json()
        
        if 'choices' in response_data and response_data['choices']:
            first_choice = response_data['choices'][0]
            if 'prompt_logprobs' in first_choice:
                return first_choice['prompt_logprobs']
                
        logger.error("No prompt logprobs found in response")
        return []
        
    except Exception as e:
        logger.error(f"Error getting prompt logprobs: {str(e)}")
        return []

async def _query_completions(
    data: Dict[str, Any],
    server_name: str = "llm_server",
    timeout: int = 5
) -> httpx.Response:

    url = f"http://{server_name}:{AI_SERVER_PORT}/completions"
    
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
        logger.error(f"HTTP error {e.response.status_code} from completions endpoint: {str(e)}")
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