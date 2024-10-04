import gc
import os
from time import sleep
import signal
import multiprocessing

import torch
from vllm.distributed.parallel_state import destroy_model_parallel
from huggingface_hub import scan_cache_dir

from app.logging import logging
from app import models
from app.inference import engines, completions
from app.models import RequestInfo

from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException
import asyncio
from typing import Optional
import httpx
import uvicorn
import errno


class CancelledErrorFilter:
    def __call__(self, record):
        if record["exception"]:
            exc_type, _, _ = record["exception"]
            if exc_type is asyncio.exceptions.CancelledError:
                return False
        return True


logging.add(lambda msg: None, filter=CancelledErrorFilter())
multiprocessing.set_start_method("spawn", force=True)


class EngineState:
    def __init__(self):
        self.current_model: Optional[str] = None
        self.model_ready = multiprocessing.Event()
        self.model_loaded = False
        self.toxic_checker: Optional[models.ToxicEngine] = None
        self.model_process: Optional[multiprocessing.Process] = None

    async def load_model_and_tokenizer(
        self,
        model_to_load: str,
        revision: str,
        tokenizer_name: str,
        half_precision: bool,
        force_reload: bool,
        gpu_memory_utilization: float,
        max_model_len: int,
        tensor_parallel_size: int,
        num_scheduler_steps: int
    ) -> None:
        if self.model_loaded and not force_reload and self.current_model == model_to_load:
            logging.info(f"Model {model_to_load} already loaded")
            return

        await self._unload_model()

        self.model_ready.clear()
        ctx = multiprocessing.get_context("spawn")
        self.model_process = ctx.Process(
            target=self._model_server_process,
            args=(
                model_to_load,
                revision,
                tokenizer_name,
                half_precision,
                self.model_ready,
                gpu_memory_utilization,
                max_model_len,
                tensor_parallel_size,
                num_scheduler_steps
            ),
        )
        self.model_process.start()
        self.model_ready.wait()
        self.current_model = model_to_load
        self.model_loaded = True
        logging.info(f"Loaded new model {model_to_load} ✅")

    async def _unload_model(self) -> None:
        if self.model_process is not None:
            try:
                self.model_process.terminate()
                self.model_process.join(timeout=10)
            except TimeoutError:
                os.kill(self.model_process.pid, signal.SIGKILL)
                sleep(5)
            logging.info("Terminated previous model loading process")

        self.model_loaded = False
        self.current_model = None
        destroy_model_parallel()
        gc.collect()
        torch.cuda.empty_cache()

        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        logging.info("Unloaded model")

    def _model_server_process(
        self,
        model_name: str,
        revision: str,
        tokenizer_name: str,
        half_precision: bool,
        model_ready: multiprocessing.Event,
        gpu_memory_utilization: float,
        max_model_len: int,
        tensor_parallel_size: int,
        num_scheduler_steps: int
    ) -> None:
        logging.add(lambda msg: None, filter=CancelledErrorFilter())
        app = FastAPI()
        engine_holder = {}

        @app.post("/generate")
        async def generate_text(request: RequestInfo):
            try:
                logging.info(f"Received request: {request.json()}")
                llm_engine = engine_holder["engine"]

                async def stream_response():
                    async for chunk in completions.complete_vllm(llm_engine, request):
                        yield chunk

                return StreamingResponse(stream_response(), media_type="application/json")
            except Exception as e:
                logging.error(f"Error during text generation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        async def load_model():
            gc.collect()
            torch.cuda.empty_cache()
            try:
                llm_engine = await engines.get_llm_engine(
                    model_name,
                    revision,
                    tokenizer_name,
                    half_precision,
                    gpu_memory_utilization,
                    max_model_len,
                    tensor_parallel_size,
                    num_scheduler_steps
                )
            except OSError as e:
                if e.errno == errno.ENOSPC:
                    logging.info("OSError was thrown, clearing disk before loading model...")
                    self.clean_cache_hf()
                    self.llm_engine = await engines.get_llm_engine(
                        model_name,
                        revision,
                        tokenizer_name,
                        half_precision,
                        gpu_memory_utilization,
                        max_model_len,
                        tensor_parallel_size,
                        num_scheduler_steps
                    )
                else:
                    raise

            engine_holder["engine"] = llm_engine
            model_ready.set()

        logging.info("-Child- loading model")
        asyncio.run(load_model())
        logging.info("-Child- running api")
        uvicorn.run(app, host="0.0.0.0", port=6910)

    async def forward_request(self, request_info: models.RequestInfo):
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", "http://localhost:6910/generate", json=request_info.dict()) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line

    def clean_cache_hf(self):
        logging.info("Clearing HuggingFace cache dir...")
        cache_info = scan_cache_dir()
        to_clean = []
        for repo in cache_info.repos:
            to_clean += [revision.commit_hash for revision in repo.revisions]
        delete_strategy = cache_info.delete_revisions(*to_clean)
        logging.info(f"Will free {delete_strategy.expected_freed_size_str}.")
        delete_strategy.execute()
