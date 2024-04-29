#!/bin/bash

port=${PORT:-6900}

source activate venv
uvicorn --lifespan on --reload --port $port --host 0.0.0.0 app.asgi:app 

