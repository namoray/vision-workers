#!/bin/bash

port=${PORT:-6920}

uvicorn --lifespan on --reload --port $port --host 0.0.0.0 app.asgi:app 

