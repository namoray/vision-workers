#!/bin/bash


DEFAULT_ORCHESTRATOR_IMAGE="corcelio/vision:orchestrator-latest"
DEFAULT_LLM_IMAGE="corcelio/vision:llm_server-latest"
DEFAULT_IMAGE_SERVER_IMAGE="corcelio/vision:image_server-latest"

ORCHESTRATOR_IMAGE=${1:-$DEFAULT_ORCHESTRATOR_IMAGE}
LLM_IMAGE=${2:-$DEFAULT_LLM_IMAGE}
IMAGE_SERVER_IMAGE=${3:-$DEFAULT_IMAGE_SERVER_IMAGE}

ORCHESTRATOR_PORT=6920

NETWORK="comm"
ORCHESTRATOR_CONTAINER_NAME="orchestrator"

DOCKER_RUN_FLAGS="--rm \
                  --gpus all \
                  --runtime=nvidia \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  -e LLM_SERVER_DOCKER_IMAGE=$LLM_IMAGE \
                  -e IMAGE_SERVER_DOCKER_IMAGE=$IMAGE_SERVER_IMAGE \
                  --network $NETWORK"

docker volume inspect HF > /dev/null 2>&1 || docker volume create HF
docker volume inspect COMFY > /dev/null 2>&1 || docker volume create COMFY

docker network inspect $NETWORK > /dev/null 2>&1 || docker network create $NETWORK

docker run -d --name $ORCHESTRATOR_CONTAINER_NAME $DOCKER_RUN_FLAGS -p $ORCHESTRATOR_PORT:$ORCHESTRATOR_PORT $ORCHESTRATOR_IMAGE
