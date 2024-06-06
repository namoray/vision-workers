CONFIG_CONTENT=$(cat ./cicd_config.json)

GCP_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-workflow"')
echo "GCP_ENABLED=$GCP_ENABLED" >> $GITHUB_ENV

GCP_GPU_NAME=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-gpu-name"')
echo "GCP_GPU_NAME=$GCP_GPU_NAME" >> $GITHUB_ENV

GCP_GPU_ZONE=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-gpu-zone"')
echo "GCP_GPU_ZONE=$GCP_GPU_ZONE" >> $GITHUB_ENV

ORCH_PORT=$(echo "$CONFIG_CONTENT" | jq -r '."orchestrator-port"')
echo "ORCH_PORT=$ORCH_PORT" >> $GITHUB_ENV

LLM_PORT=$(echo "$CONFIG_CONTENT" | jq -r '."llm-server-port"')
echo "LLM_PORT=$LLM_PORT" >> $GITHUB_ENV

IMAGE_PORT=$(echo "$CONFIG_CONTENT" | jq -r '."image-server-port"')
echo "IMAGE_PORT=$IMAGE_PORT" >> $GITHUB_ENV

RUNPOD_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-workflow"')
echo "RUNPOD_ENABLED=$RUNPOD_ENABLED" >> $GITHUB_ENV
