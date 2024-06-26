#!/bin/bash

usage() {
    echo "Usage: $0 -o ORCHESTRATOR_IMAGE -l LLM_IMAGE -i IMAGE_SERVER_IMAGE"
    echo "Optional: -d DESTINATION_PREFIX (default: corcelio/vision)"
    echo "Optional: -s SUFFIX (default: latest)"
    exit 1
}

# Default values
DEST_PREFIX="corcelio/vision"
SUFFIX="latest"

while getopts "o:l:i:d:s:" opt; do
    case $opt in
        o) ORCHESTRATOR_IMAGE="$OPTARG" ;;
        l) LLM_IMAGE="$OPTARG" ;;
        i) IMAGE_SERVER_IMAGE="$OPTARG" ;;
        d) DEST_PREFIX="$OPTARG" ;;
        s) SUFFIX="$OPTARG" ;;
        *) usage ;;
    esac
done

if [ -z "$ORCHESTRATOR_IMAGE" ] || [ -z "$LLM_IMAGE" ] || [ -z "$IMAGE_SERVER_IMAGE" ]; then
    usage
fi

ORCHESTRATOR_TAG="$DEST_PREFIX:orchestrator-$SUFFIX"
LLM_TAG="$DEST_PREFIX:llm_server-$SUFFIX"
IMAGE_SERVER_TAG="$DEST_PREFIX:image_server-$SUFFIX"

# Prompt for Docker Hub credentials
read -p "Docker Hub Username: " DOCKER_USER
read -s -p "Docker Hub Password: " DOCKER_PASS
echo

# Login to Docker Hub
echo "Logging in to Docker Hub..."
echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
if [ $? -ne 0 ]; then
    echo "Error: Docker login failed"
    exit 1
fi

tag_and_push() {
    local SOURCE_IMAGE=$1
    local DEST_TAG=$2

    echo "Pulling $SOURCE_IMAGE"
    docker pull $SOURCE_IMAGE
    if [ $? -ne 0 ]; then
        echo "Error: Failed to pull $SOURCE_IMAGE"
        return 1
    fi

    echo "Tagging $SOURCE_IMAGE as $DEST_TAG"
    docker tag $SOURCE_IMAGE $DEST_TAG
    if [ $? -ne 0 ]; then
        echo "Error: Failed to tag $SOURCE_IMAGE as $DEST_TAG"
        return 1
    fi

    echo "Pushing $DEST_TAG"
    docker push $DEST_TAG
    if [ $? -ne 0 ]; then
        echo "Error: Failed to push $DEST_TAG"
        return 1
    fi

    return 0
}

tag_and_push $ORCHESTRATOR_IMAGE $ORCHESTRATOR_TAG
ORCHESTRATOR_RESULT=$?

tag_and_push $LLM_IMAGE $LLM_TAG
LLM_RESULT=$?

tag_and_push $IMAGE_SERVER_IMAGE $IMAGE_SERVER_TAG
IMAGE_SERVER_RESULT=$?

echo "Summary of actions:"
if [ $ORCHESTRATOR_RESULT -eq 0 ]; then
    echo "Orchestrator image ($ORCHESTRATOR_IMAGE) tagged and pushed as:"
    echo "  $ORCHESTRATOR_TAG"
else
    echo "Failed to process orchestrator image ($ORCHESTRATOR_IMAGE)"
fi

if [ $LLM_RESULT -eq 0 ]; then
    echo "LLM image ($LLM_IMAGE) tagged and pushed as:"
    echo "  $LLM_TAG"
else
    echo "Failed to process LLM image ($LLM_IMAGE)"
fi

if [ $IMAGE_SERVER_RESULT -eq 0 ]; then
    echo "Image server image ($IMAGE_SERVER_IMAGE) tagged and pushed as:"
    echo "  $IMAGE_SERVER_TAG"
else
    echo "Failed to process image server image ($IMAGE_SERVER_IMAGE)"
fi

echo "-------------------------------------"
echo "Summary:"
echo "-------------------------------------"
[ $ORCHESTRATOR_RESULT -eq 0 ] && echo "Source: $ORCHESTRATOR_IMAGE -> Destination: $ORCHESTRATOR_TAG"
[ $LLM_RESULT -eq 0 ] && echo "Source: $LLM_IMAGE -> Destination: $LLM_TAG"
[ $IMAGE_SERVER_RESULT -eq 0 ] && echo "Source: $IMAGE_SERVER_IMAGE -> Destination: $IMAGE_SERVER_TAG"
echo "-------------------------------------"

if [ $ORCHESTRATOR_RESULT -ne 0 ] || [ $LLM_RESULT -ne 0 ] || [ $IMAGE_SERVER_RESULT -ne 0 ]; then
    exit 1
fi

echo "All images processed successfully."