
# Setting up CUDA 11.8 on Ubuntu 22.04

This section provides a step-by-step guide to install CUDA 11.8 (drivers, toolkit & other libraries) Ubuntu 22.04

## Prerequisites

- Ensure your system has a CUDA-capable GPU.

## Table of Contents

- [Setting up CUDA 11.8 on Ubuntu 22.04](#setting-up-cuda-118-on-ubuntu-2204)
  - [Prerequisites](#prerequisites)
  - [Table of Contents](#table-of-contents)
  - [Steps](#steps)

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
sudo apt install ubuntu-drivers-common
ubuntu-drivers devices
```

7. **Install NVIDIA driver (e.g version 535)**

```bash
sudo apt install libnvidia-common-535 libnvidia-gl-535 nvidia-driver-535 -y
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
sudo apt --fix-broken install
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

=> If you keep having broken packages issues at this point, run this to solve it 
```bash
sudo apt --fix-broken install -y
if [ $? -ne 0 ]; then
   conflicting_packages=$(sudo dpkg -l | grep -E 'nvidia-kernel-common|nvidia-compute-utils |nvidia-firmware' | awk '{print $2}')
   for pkg in $conflicting_packages; do
      sudo dpkg --purge --force-all $pkg
   done
   sudo dpkg --configure -a
   sudo apt-get autoremove -y
   sudo apt-get clean
   sudo apt-get update
   sudo apt-get install -f -y
   sudo apt-get upgrade -y
fi
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

14. **Verify the installation**

```bash
nvidia-smi
nvcc -V
```

15. **Install docker**
```
# Add Docker's official GPG key:
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux /ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y

# install docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

15. **NVIDIA Container Toolkit - Add the NVIDIA GPG key**

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
&& curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
   sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
   sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

16. **NVIDIA Container Toolkit - Install package**

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

17. **NVIDIA Container Toolkit - Configuring Docker to Use NVIDIA GPUs**

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