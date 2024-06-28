#!/bin/bash

# Define repository URL
REPO_URL="https://github.com/vllm-project/vllm.git"
LOCAL_DIR="vllm-local"

# Step 1: Clone the VLLM repository (if not already cloned)
if [ ! -d "$LOCAL_DIR" ]; then
    git clone $REPO_URL $LOCAL_DIR
    echo "Repository cloned."
else
    echo "Repository already exists locally. Pulling any new changes."
    cd $LOCAL_DIR
    git pull origin main
    cd ..
fi

cd $LOCAL_DIR

# checkout to a branch where vllm worked for cuda118 patch
git checkout 93348d9458af7517bb8c114611d438a1b4a2c3be

#------- cuda 11.8 patch-------
SETUP_FILE_PATH="setup.py"
TOMl_FILE="pyproject.toml"
rm -f $TOMl_FILE
sed -i '0,/MAIN_CUDA_VERSION = "12.1"/s//MAIN_CUDA_VERSION = "11.8"/' "$SETUP_FILE_PATH"
pip install -U xformers==0.0.23.post1 torchvision torch  --index-url https://download.pytorch.org/whl/cu118
sed -i '/torch/d' requirements.txt
sed -i '/xformers/d' requirements.txt
pip install packaging
#-----------------------------

pip install -e .

echo "VLLM library installed in editable mode. Changes applied successfully."

# Return to the original directory
cd ..

