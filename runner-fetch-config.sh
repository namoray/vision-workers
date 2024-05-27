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

TEST_JSON_FOLDER=$(echo "$CONFIG_CONTENT" | jq -r '."test-json-folder"')
echo "TEST_JSON_FOLDER=$TEST_JSON_FOLDER" >> $GITHUB_ENV

TEST_GCP_ORCH_TXT2IMG=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-orch-text2image"')
echo "TEST_GCP_ORCH_TXT2IMG=$TEST_GCP_ORCH_TXT2IMG" >> $GITHUB_ENV

TEST_GCP_ORCH_AVATAR=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-orch-avatar"')
echo "TEST_GCP_ORCH_AVATAR=$TEST_GCP_ORCH_AVATAR" >> $GITHUB_ENV

TEST_GCP_LLM_LOAD=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-llm-load-model"')
echo "TEST_GCP_LLM_LOAD=$TEST_GCP_LLM_LOAD" >> $GITHUB_ENV

TEST_GCP_LLM_QUERY=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-llm-query-model"')
echo "TEST_GCP_LLM_QUERY=$TEST_GCP_LLM_QUERY" >> $GITHUB_ENV

TEST_GCP_IMAGE_TXT2IMG=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-image-text2image"')
echo "TEST_GCP_IMAGE_TXT2IMG=$TEST_GCP_IMAGE_TXT2IMG" >> $GITHUB_ENV

TEST_GCP_IMAGE_AVATAR=$(echo "$CONFIG_CONTENT" | jq -r '."gcp-test-image-avatar"')
echo "TEST_GCP_IMAGE_AVATAR=$TEST_GCP_IMAGE_AVATAR" >> $GITHUB_ENV

RUNPOD_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-workflow"')
echo "RUNPOD_ENABLED=$RUNPOD_ENABLED" >> $GITHUB_ENV

RUNPOD_GPU_TYPE=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-gpu-type"')
echo "RUNPOD_GPU_TYPE=$RUNPOD_GPU_TYPE" >> $GITHUB_ENV

RUNPOD_TEST_ORCH_TXT2IMG=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-orch-text2image"')
echo "RUNPOD_TEST_ORCH_TXT2IMG=$RUNPOD_TEST_ORCH_TXT2IMG" >> $GITHUB_ENV

RUNPOD_TEST_ORCH_LLM=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-orch-llm"')
echo "RUNPOD_TEST_ORCH_LLM=$RUNPOD_TEST_ORCH_LLM" >> $GITHUB_ENV

RUNPOD_TEST_LLM_LOAD=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-llm-load-model"')
echo "RUNPOD_TEST_LLM_LOAD=$RUNPOD_TEST_LLM_LOAD" >> $GITHUB_ENV

RUNPOD_TEST_LLM_QUERY=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-llm-query-model"')
echo "RUNPOD_TEST_LLM_QUERY=$RUNPOD_TEST_LLM_QUERY" >> $GITHUB_ENV

RUNPOD_TEST_IMAGE_TXT2IMG=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-image-text2image"')
echo "RUNPOD_TEST_IMAGE_TXT2IMG=$RUNPOD_TEST_IMAGE_TXT2IMG" >> $GITHUB_ENV

RUNPOD_TEST_IMAGE_AVATAR=$(echo "$CONFIG_CONTENT" | jq -r '."runpod-test-image-avatar"')
echo "RUNPOD_TEST_IMAGE_AVATAR=$RUNPOD_TEST_IMAGE_AVATAR" >> $GITHUB_ENV