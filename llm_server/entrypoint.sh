#!/bin/bash

source activate venv
uvicorn --lifespan on --port 6919 --host 0.0.0.0  app.asgi:app

