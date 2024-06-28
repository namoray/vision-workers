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

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --no-runtime-flag) NO_RUNTIME_FLAG=1 ;;
        --device) DEVICE="$2"; shift ;;
        *) ;;
    esac
    shift
done

DOCKER_RUN_FLAGS="--rm \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  -e LLM_SERVER_DOCKER_IMAGE=$LLM_IMAGE \
                  -e IMAGE_SERVER_DOCKER_IMAGE=$IMAGE_SERVER_IMAGE \
                  --network $NETWORK"

# Add the --runtime=nvidia flag unless --no-runtime-flag is specified
if [[ -z "$NO_RUNTIME_FLAG" ]]; then
    DOCKER_RUN_FLAGS+=" --runtime=nvidia"
fi

if [[ -n "$DEVICE" ]]; then
    DOCKER_RUN_FLAGS+=" -e CUDA_VISIBLE_DEVICES=$DEVICE \
                        -e DEVICE=$DEVICE \
                        --gpus \"device=$DEVICE\""
else
    DOCKER_RUN_FLAGS+=" --gpus all"
fi


check_and_pull_image() {
  IMAGE=$1

  get_local_image_digest() {
    DIGEST=$(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}' 2>/dev/null | cut -d'@' -f2)
    echo $DIGEST
  }

  LOCAL_DIGEST=$(get_local_image_digest)

  if [ -z "$LOCAL_DIGEST" ]; then
    echo "Image $IMAGE does not exist locally. Pulling from Docker Hub..."
    docker pull $IMAGE
  else
    echo "Image $IMAGE exists locally. Checking for updates..."
    docker pull $IMAGE
    REMOTE_DIGEST=$(get_local_image_digest)
    if [ "$REMOTE_DIGEST" != "$LOCAL_DIGEST" ]; then
      echo "A new version of the image $IMAGE is available and has been pulled."
    else
      echo "The image $IMAGE is up-to-date."
    fi
  fi
}

check_and_pull_image $ORCHESTRATOR_IMAGE
check_and_pull_image $LLM_IMAGE
check_and_pull_image $IMAGE_SERVER_IMAGE

docker volume inspect HF > /dev/null 2>&1 || docker volume create HF
docker volume inspect COMFY > /dev/null 2>&1 || docker volume create COMFY

docker network inspect $NETWORK > /dev/null 2>&1 || docker network create $NETWORK

docker run -d --rm --name $ORCHESTRATOR_CONTAINER_NAME $DOCKER_RUN_FLAGS -p $ORCHESTRATOR_PORT:$ORCHESTRATOR_PORT $ORCHESTRATOR_IMAGE
