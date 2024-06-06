
# Setting up CUDA 11.8 on Ubuntu 22.04

This section provides a step-by-step guide to install CUDA 11.8 (drivers, toolkit & other libraries) Ubuntu 22.04

## Prerequisites

- Ensure your system has a CUDA-capable GPU.

## Table of Contents

- [Setting up CUDA 11.8 on Ubuntu 22.04](#setting-up-cuda-118-on-ubuntu-2204)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
    - [Verify your GPU is CUDA-capable](#verify-your-gpu-is-cuda-capable)
    - [Remove previous NVIDIA installations](#remove-previous-nvidia-installations)
    - [Update your system](#update-your-system)
    - [Install required packages](#install-required-packages)
    - [Add the NVIDIA PPA repository and update](#add-the-nvidia-ppa-repository-and-update)
    - [Find recommended driver versions for you](#find-recommended-driver-versions-for-you)
    - [Install NVIDIA driver (e.g. version 515)](#install-nvidia-driver-eg-version-515)
    - [Reboot your system](#reboot-your-system)
    - [Verify the NVIDIA driver installation](#verify-the-nvidia-driver-installation)
    - [Download and set up CUDA repository](#download-and-set-up-cuda-repository)
    - [Update and upgrade](#update-and-upgrade)
    - [Install CUDA 11.8](#install-cuda-118)
    - [Set up environment variables](#set-up-environment-variables)
    - [Install cuDNN 8.7](#install-cudnn-87)
    - [Verify the installation](#verify-the-installation)
    - [NVIDIA Container Toolkit - Add the NVIDIA GPG key](#nvidia-container-toolkit---add-the-nvidia-gpg-key)
    - [NVIDIA Container Toolkit - Install package](#nvidia-container-toolkit---install-package)
    - [NVIDIA Container Toolkit - Configuring Docker to Use NVIDIA GPUs](#nvidia-container-toolkit---configuring-docker-to-use-nvidia-gpus)
    - [If any problems arrive with 'docker run' using GPUs, try this](#if-any-problems-arrive-with-docker-run-using-gpus-try-this)

## Steps

1. **Verify your GPU is CUDA-capable**

   ```bash
   lspci | grep -i nvidia
   ```

2. **Remove previous NVIDIA installations**

   ```bash
   sudo apt purge nvidia* -y
   sudo apt remove nvidia-* -y
   sudo rm /etc/apt/sources.list.d/cuda*
   sudo apt autoremove -y && sudo apt autoclean -y
   sudo rm -rf /usr/local/cuda*
   ```

3. **Update your system**

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Install required packages**

   ```bash
   sudo apt install g++ freeglut3-dev build-essential libx11-dev libxmu-dev libxi-dev libglu1-mesa libglu1-mesa-dev
   ```

5. **Add the NVIDIA PPA repository and update**

   ```bash
   sudo add-apt-repository ppa:graphics-drivers/ppa
   sudo apt update
   ```

6. **find recommended driver versions for you**
   ```bash
   ubuntu-drivers devices
   ```

7. **Install NVIDIA driver (e.g version 515)**

   ```bash
   sudo apt install libnvidia-common-515 libnvidia-gl-515 nvidia-driver-515 -y
   ```

8. **Reboot your system**

   ```bash
   sudo reboot now
   ```

9. **Verify the NVIDIA driver installation**

   ```bash
   nvidia-smi
   ```

10. **Download and set up CUDA repository**

   ```bash
   sudo wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
   sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
   sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /"
   ```

11. **Update and upgrade**

    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

12. **Install CUDA 11.8**

    ```bash
    sudo apt install cuda-11-8 -y
    ```

13. **Set up environment variables**

    ```bash
    echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
    source ~/.bashrc
    sudo ldconfig
    ```

14. **Install cuDNN 8.7**

    - Register at [NVIDIA Developer](https://developer.nvidia.com/developer-program/signup) and download cuDNN.

    ```bash
    CUDNN_TAR_FILE="cudnn-linux-x86_64-8.7.0.84_cuda11-archive.tar.xz"
    sudo wget https://developer.download.nvidia.com/compute/redist/cudnn/v8.7.0/local_installers/11.8/${CUDNN_TAR_FILE}
    sudo tar -xvf ${CUDNN_TAR_FILE}
    sudo mv cudnn-linux-x86_64-8.7.0.84_cuda11-archive cuda

    sudo cp -P cuda/include/cudnn.h /usr/local/cuda-11.8/include
    sudo cp -P cuda/lib/libcudnn* /usr/local/cuda-11.8/lib64/
    sudo chmod a+r /usr/local/cuda-11.8/lib64/libcudnn*
    ```

15. **Verify the installation**

    ```bash
    nvidia-smi
    nvcc -V
    ```

16. **NVIDIA Container Toolkit - Add the NVIDIA GPG key**

    ```bash
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    ```

17. **NVIDIA Container Toolkit - Install package**

    ```bash
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
    ```

18. **NVIDIA Container Toolkit - Configuring Docker to Use NVIDIA GPUs**

    ```bash
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   nvidia-ctk runtime configure --runtime=docker --config=$HOME/.config/docker/daemon.json
   systemctl --user restart docker
    ```

18. **If any problems arrive with 'docker run' using GPUs, try this**

    ```bash
   sudo nano /etc/docker/daemon.json
   # Change to the following configuration:
   {
   "default-runtime": "nvidia",
   "runtimes": {
      "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
      }
   }
   }

   # restart service 
   sudo systemctl restart docker
    ```