#!/bin/bash


source activate venv
uvicorn --lifespan on --reload --port 6920 --host 0.0.0.0 app.asgi:app 

