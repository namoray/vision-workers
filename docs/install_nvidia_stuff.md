```bash
sudo apt install nvidia-cuda-toolkit  # (You might need to restart services when prompted)

# Now install nvidia runtime
CUDA_VERSION="12.2.0"
conda install nvidia/label/cuda-$CUDA_VERSION::cuda-toolkit -y

distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install nvidia-docker2

which nvidia-container-runtime

sudo systemctl restart docker
```



If you still have problems with docker running with `unknown or invalid runtime name: nvidia`, try this:

```bash
apt-get install ubuntu-drivers-common \
	&& sudo ubuntu-drivers autoinstall

# reboot
sudo reboot now

curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
apt-get install nvidia-container-runtime
sudo systemctl restart docker
```