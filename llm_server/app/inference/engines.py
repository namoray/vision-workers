import torch
from vllm import AsyncEngineArgs, AsyncLLMEngine
from app.logging import logging
from app.utils import determine_needs_await
from app import models
from typing import Optional
from app.inference import completions


async def _get_vllm_engine(
    model_name: str,
    revision: str,
    tokenizer_name: str,
    half_precision: bool,
    gpu_memory_utilization: float = 0.8,
    max_model_len: int = None,
    tensor_parallel_size: int = 1,
    num_scheduler_steps: int = 1
) -> models.LLMEngine:
    if half_precision:
        dtype = "float16"
    else:
        dtype = "float32"
    logging.info(f"Loading model {model_name} with dtype {dtype}")
    engine_args = AsyncEngineArgs(
        model=model_name,
        tokenizer=tokenizer_name,
        dtype=dtype,
        enforce_eager=False,
        revision=revision,
        max_num_seqs=256,
        enable_chunked_prefill=True,
        # max_num_batched_tokens=128,
        max_logprobs=100,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        trust_remote_code=True,
        tensor_parallel_size=tensor_parallel_size,
        num_scheduler_steps=num_scheduler_steps
    )
    model_instance = AsyncLLMEngine.from_engine_args(engine_args)

    cuda_version = torch.version.cuda
    if determine_needs_await(cuda_version):
        logging.info(f"Cuda version :  {cuda_version}, awaiting for tokenizer init")
        tokenizer_obj = await model_instance.get_tokenizer()
    else:
        logging.info(f"Cuda version :  {cuda_version}, not awaiting for tokenizer init")
        tokenizer_obj = model_instance.get_tokenizer()

    logging.info(f"Model initialized successfully with {model_name} using vLLM")
    return models.LLMEngine(
        tokenizer=tokenizer_obj,
        model_name=model_name,
        tokenizer_name=tokenizer_name,
        model=model_instance,
        completion_method=completions.complete_vllm,
        maxlogprobs=10,
    )


async def get_llm_engine(
    model_name: str,
    revision: str,
    tokenizer_name: Optional[str] = None,
    half_precision: bool = True,
    gpu_memory_utilization: float = 0.8,
    max_model_len: int = None,
    tensor_parallel_size: int = 1, 
    num_scheduler_steps: int = 1
) -> models.LLMEngine:
    # if "llava" not in model_name:
    # try:
    if tokenizer_name is None:
        tokenizer_name = model_name

    return await _get_vllm_engine(
        model_name,
        revision,
        tokenizer_name,
        half_precision,
        gpu_memory_utilization,
        max_model_len,
        tensor_parallel_size,
        num_scheduler_steps
    )
