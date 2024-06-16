#!/bin/bash

ORCHESTRATOR_CONTAINER_NAME="validator"
DEFAULT_ORCHESTRATOR_IMAGE="corcelio/vision:orchestrator-latest"
DEFAULT_LLM_IMAGE="corcelio/vision:llm_server-latest"
DEFAULT_IMAGE_SERVER_IMAGE="corcelio/vision:image_server-latest"

ORCHESTRATOR_IMAGE="${1:-$DEFAULT_ORCHESTRATOR_IMAGE}"
LLM_IMAGE="${2:-$DEFAULT_LLM_IMAGE}"
IMAGE_SERVER_IMAGE="${3:-$DEFAULT_IMAGE_SERVER_IMAGE}"

SERVICE_IMAGES=(
    "$LLM_IMAGE"
    "$IMAGE_SERVER_IMAGE"
    # Add new service images here as needed
)

ORCHESTRATOR_PORT=6920
SERVICE_PORT=6919
NETWORK="comm"

# add new service here as well
DOCKER_RUN_FLAGS="--rm \
                  --gpus all \
                  --runtime=nvidia \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  -e LLM_SERVER_DOCKER_IMAGE=$LLM_IMAGE \
                  -e IMAGE_SERVER_DOCKER_IMAGE=$IMAGE_SERVER_IMAGE \
                  --network $NETWORK"


CHECK_INTERVAL=60 # Interval to check for docker image updates
LOG_STREAM_DURATION=10  # Duration to stream logs
RETRY_INTERVAL=5 # Time to wait between critical cmds retry
RETRY_LIMIT=5 # Number of maximum retries for critical cmds
SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SCRIPT_NAME=$(basename "$SCRIPT_PATH")

log() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message"
}

retry_command() {
    local cmd="$1"
    local retries=0

    until $cmd; do
        retries=$((retries + 1))
        if [ $retries -ge $RETRY_LIMIT ]; then
            log "Retry limit reached for command: $cmd. Continuing with the next step."
            return 1
        fi
        log "Command failed: $cmd. Retrying in $RETRY_INTERVAL seconds..."
        sleep $RETRY_INTERVAL
    done

    return 0
}

wait_for_port_release() {
    local port="$1"
    while sudo netstat -tuln | grep -q ":$port "; do
        log "Port $port is still in use. Waiting..."
        sleep 1
    done
    log "Port $port is now free."
}

check_and_update_script() {
    log "Checking for updates to the script..."

    # Fetch changes from the remote repository and store the output
    sudo -u $USER git stash
    PULL_OUTPUT=$(sudo -u $USER git pull)

    # Check if the script file is mentioned in the pull output
    if echo "$PULL_OUTPUT" | grep -q "$SCRIPT_NAME"; then
        log "New version of the script found in pull description. Updating..."
        log "$PULL_OUTPUT"
        chmod +x "$SCRIPT_PATH"
        exec "$SCRIPT_PATH" "$@"
    else
        log "No updates found for the script."
    fi
}

check_and_update_containers() {
    log "Checking for updates to Docker images..."

    local images=(
        "$ORCHESTRATOR_IMAGE"
        "${SERVICE_IMAGES[@]}"
    )

    for image in "${images[@]}"; do
        if retry_command "docker pull $image"; then
            log "Pulled the latest image: $image"
        else
            log "Failed to pull the latest image after several attempts: $image"
        fi
    done

    # Get the image ID of the running orchestrator container
    local running_image_id
    running_image_id=$(docker inspect --format='{{.Image}}' $ORCHESTRATOR_CONTAINER_NAME 2>/dev/null)
    if [ $? -ne 0 ]; then
        log "Failed to get the running image ID. Skipping update check."
        return
    fi

    # Get the image ID of the latest orchestrator image
    local latest_image_id
    latest_image_id=$(docker inspect --format='{{.Id}}' $ORCHESTRATOR_IMAGE 2>/dev/null)
    if [ $? -ne 0 ]; then
        log "Failed to get the latest image ID. Skipping update check."
        return
    fi

    # Compare the image IDs and restart the container if they are different
    if [ "$running_image_id" != "$latest_image_id" ]; then
        log "New orchestrator image detected. Restarting the orchestrator container..."

        if retry_command "docker stop $ORCHESTRATOR_CONTAINER_NAME"; then
            log "Stopped the orchestrator container."
        else
            log "Failed to stop the orchestrator container after several attempts. Continuing with removal."
        fi

        # Remove the stopped container
        if retry_command "docker rm $ORCHESTRATOR_CONTAINER_NAME"; then
            log "Removed the old orchestrator container."
        else
            log "Failed to remove the old orchestrator container after several attempts."
        fi

        # Wait for ports to be released
        wait_for_port_release $ORCHESTRATOR_PORT
        wait_for_port_release $SERVICE_PORT

        # Run the new container in detached mode
        if retry_command "docker run -d --name $ORCHESTRATOR_CONTAINER_NAME $DOCKER_RUN_FLAGS -p $ORCHESTRATOR_PORT:$ORCHESTRATOR_PORT $ORCHESTRATOR_IMAGE"; then
            log "Started the new orchestrator container."
        else
            log "Failed to start the new orchestrator container after several attempts."
        fi
    else
        log "No new updates found for the orchestrator container."
    fi
}

stream_logs() {
    timeout $LOG_STREAM_DURATION docker logs -f --tail 50 $ORCHESTRATOR_CONTAINER_NAME
}

initialize_container() {
    # Create Docker volumes for the orchestrator and services if they do not exist
    local volumes=(
        "COMFY"
        "HF"
    )

    for volume in "${volumes[@]}"; do
        if ! docker volume ls --format '{{.Name}}' | grep -q "^$volume$"; then
            if retry_command "docker volume create $volume"; then
                log "Created Docker volume: $volume"
            else
                log "Failed to create Docker volume: $volume after several attempts."
            fi
        else
            log "Docker volume already exists: $volume"
        fi
    done

    # create network
    docker network create $NETWORK

    # Run validator container if not already running
    if ! docker ps --format '{{.Names}}' | grep -q "^${ORCHESTRATOR_CONTAINER_NAME}$"; then

        if docker run -d --name $ORCHESTRATOR_CONTAINER_NAME $DOCKER_RUN_FLAGS -p $ORCHESTRATOR_PORT:$ORCHESTRATOR_PORT $ORCHESTRATOR_IMAGE; then
            log "Started initial validator container."
        else
            log "Failed to start initial validator container. Checking for existing container with same name."
            if docker ps -a --format '{{.Names}}' | grep -q "^${ORCHESTRATOR_CONTAINER_NAME}$"; then
                log "Container with name $ORCHESTRATOR_CONTAINER_NAME already exists. Removing it."
                if docker rm -f $ORCHESTRATOR_CONTAINER_NAME; then
                    log "Successfully removed existing container $ORCHESTRATOR_CONTAINER_NAME. Attempting to start container again."
                    wait_for_port_release $ORCHESTRATOR_PORT
                    wait_for_port_release $SERVICE_PORT
                    if docker run -d --name $ORCHESTRATOR_CONTAINER_NAME $DOCKER_RUN_FLAGS -p $ORCHESTRATOR_PORT:$ORCHESTRATOR_PORT $ORCHESTRATOR_IMAGE; then
                        log "Started initial validator container."
                    else
                        log "Failed to start initial validator container after removing existing container."
                    fi
                else
                    log "Failed to remove existing container $ORCHESTRATOR_CONTAINER_NAME."
                fi
            fi
        fi
    else
        log "Validator container is already running."
    fi
}

main_loop() {
    while true; do
        check_and_update_script
        check_and_update_containers
        echo "Latest container logs:"
        echo "------------------------------------"
        stream_logs
        echo "------------------------------------"
    sleep $CHECK_INTERVAL
done
}

initialize_container
main_loop
