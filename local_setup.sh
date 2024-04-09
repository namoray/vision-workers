#!/bin/bash

# THIS IS A FILE TO USE TO RUN THE CODE LOCALLY WITHOUT THE DOCKER TEMPALTE - I DOUBT YOU NEED THIS

# Stop script on error
set -e

# Update system and install required packages

sudo chmod 1777 /tmp


sudo apt-get update && sudo apt-get install -y software-properties-common 
sudo apt-get update && sudo apt-get install -y lsof
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt install -y python3.10-dev

sudo apt-get update \
    && sudo apt-get upgrade -y \
    && sudo apt-get -y full-upgrade \
    && sudo apt-get -y install python3-dev \
    && sudo apt-get install -y --no-install-recommends \
        build-essential \
        # python3-pip\
        apt-utils \
        curl \
        wget \
        vim \
        sudo \
        git \
        ffmpeg \
        libsm6 \
        libxext6 \
        python3-tk \
        python3-dev \
        git-lfs \
        unzip \
    && sudo apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/*

#pm2
sudo apt-get update && \
sudo apt-get install -y curl && \
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash - && \
sudo apt-get install -y nodejs && \
sudo npm install -g pm2


# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 700 Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda without manual intervention
./Miniconda3-latest-Linux-x86_64.sh -b -u

# Initialize Conda in the current shell
source "$HOME/miniconda3/etc/profile.d/conda.sh"

# Install reqs
conda create -n venv python=3.10.13 -y
conda activate venv
pip install -r llm_server/requirements.txt
pip install -r image_server/requirements.txt
pip install -r validator_orchestrator/requirements.txt

CUDA_VERSION="11.8"

CUDA_VERSION_MAJOR=$(echo $CUDA_VERSION | cut -d'.' -f1)
CUDA_VERSION_MINOR=$(echo $CUDA_VERSION | cut -d'.' -f2)
CUDA_VERSION_SIMPLE="${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}.0"

CONDA_INSTALL_CMD="conda install nvidia/label/cuda-${CUDA_VERSION_SIMPLE}::cuda-toolkit -y"

echo "Running command: $CONDA_INSTALL_CMD"
eval $CONDA_INSTALL_CMD

echo -e "Source the conda.sh script with the following command:\nsource \$HOME/miniconda3/etc/profile.d/conda.sh\nThen, activate your environment using:\nconda activate venv"
