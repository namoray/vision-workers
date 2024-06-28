#!/bin/bash

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

DEFAULT_ORCHESTRATOR_IMAGE="corcelio/vision:orchestrator-latest"
DEFAULT_LLM_SERVER_IMAGE="corcelio/vision:llm_server-latest"
DEFAULT_IMAGE_SERVER_IMAGE="corcelio/vision:image_server-latest"

ORCHESTRATOR_IMAGE=${1:-$DEFAULT_ORCHESTRATOR_IMAGE}
LLM_SERVER_IMAGE=${2:-$DEFAULT_LLM_SERVER_IMAGE}
IMAGE_SERVER_IMAGE=${3:-$DEFAULT_IMAGE_SERVER_IMAGE}

check_and_pull_image $LLM_SERVER_IMAGE
check_and_pull_image $IMAGE_SERVER_IMAGE
check_and_pull_image $ORCHESTRATOR_IMAGE

./launch_orchestrator.sh $ORCHESTRATOR_IMAGE $LLM_SERVER_IMAGE $IMAGE_SERVER_IMAGE