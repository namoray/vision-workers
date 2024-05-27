#!/bin/bash
uvicorn --lifespan on --port 6919 --host 0.0.0.0  'llm_server.app.asgi:factory'

