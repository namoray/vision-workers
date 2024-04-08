#!/bin/bash

source activate venv
uvicorn --lifespan on --port ${VLLM_PORT} --host 0.0.0.0 app.asgi:app

