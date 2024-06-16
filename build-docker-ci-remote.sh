#!/bin/bash
set -e

disk_usage=$(df -h --output=pcent / | tail -n 1 | tr -d ' %')

if [ "$disk_usage" -gt 50 ]; then
    echo "Disk usage is above 50%, cleaning older tags for docker images..."
    docker image ls --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | grep 'corcelio/cicd' | sort -rk2 > /tmp/docker_images.txt
    latest_orchestrator=$(grep 'orchestrator-' /tmp/docker_images.txt | head -n 1 | awk '{print $1}')
    latest_image_server=$(grep 'image-server-' /tmp/docker_images.txt | head -n 1 | awk '{print $1}')
    latest_llm_server=$(grep 'llm-server-' /tmp/docker_images.txt | head -n 1 | awk '{print $1}')
    echo $latest_orchestrator >> /tmp/keep_images.txt
    echo $latest_image_server >> /tmp/keep_images.txt
    echo $latest_llm_server >> /tmp/keep_images.txt
    echo 'nvidia/cuda:11.8.0-devel-ubuntu20.04' >> /tmp/keep_images.txt
    cat /tmp/docker_images.txt | grep -v -F -f /tmp/keep_images.txt | awk '{print $1}' | xargs -r docker rmi -f
    docker system prune -f
else
    echo "Disk usage ($disk_usage %) is below or equal to 50%, no action needed."
fi

# Build & push images
docker build -f Dockerfile.orchestrator -t corcelio/cicd:orchestrator-$BUILD_ID .
docker push corcelio/cicd:orchestrator-$BUILD_ID

docker build -f Dockerfile.llm_server -t corcelio/cicd:llm_server-$BUILD_ID .
docker push corcelio/cicd:llm_server-$BUILD_ID

docker build -f Dockerfile.image_server -t corcelio/cicd:image_server-$BUILD_ID .
docker push corcelio/cicd:image_server-$BUILD_ID