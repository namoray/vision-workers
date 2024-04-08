#!/bin/bash

source activate venv

if [[ -z "${CUDA_VISIBLE_DEVICES}" ]]; then
    # CUDA_VISIBLE_DEVICES environment variable is not set, run uvicorn without setting it
    uvicorn --lifespan on --port ${VLLM_PORT} --host 0.0.0.0 app.asgi:app
else
    # CUDA_VISIBLE_DEVICES environment variable is set, run uvicorn with setting it
    CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} uvicorn --lifespan on --port ${VLLM_PORT} --host 0.0.0.0 app.asgi:app
fi
