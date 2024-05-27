```bash
sudo apt install nvidia-cuda-toolkit  # (You might need to restart services when prompted)

# Now install nvidia runtime
CUDA_VERSION="11.8.0"
conda install nvidia/label/cuda-$CUDA_VERSION::cuda-toolkit -y

distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install nvidia-docker2

which nvidia-container-runtime

sudo systemctl restart docker
```

# MAKE SURE YOU SEE 11.8 WHEN YOU RUN THIS
```bash
nvcc --version
```

