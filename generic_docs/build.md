
# Steps setup env, build and run docker image

## THIS IS TO BUID TO RUN LOCALLY, YOU WONT NEED TO DO THIS TO RUN IT. JUST FOLLOW THE READ ME IN IMAGE_SERVER/LLM_SERVER/ORCHESTRATOR

### Install cuda toolkit & drivers
```bash
# for cuda versions, choose between 12.2.0 or 11.8.0 only!
PYTHON_VERSION="3.10.13"

# Download and install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 700 Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -u

# Setup Conda environment
echo 'source "$HOME/miniconda3/etc/profile.d/conda.sh"' >> ~/.bashrc && \
echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' >> ~/.bash_profile && \
echo 'source "$HOME/miniconda3/etc/profile.d/conda.sh"' >> ~/.profile && \
source ~/.bashrc && exec bash

# Create a new Conda environment with the specified Python version
conda create -n venv python=$PYTHON_VERSION -y
echo "conda activate venv" >> ~/.bashrc
source ~/.bashrc

CUDA_VERSION="12.2.0"
# Install CUDA toolkit with the specified version
conda install nvidia/label/cuda-$CUDA_VERSION::cuda-toolkit -y

distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install nvidia-docker2

# This should not be empty
which nvidia-container-runtime

```

### Install Docker
```bash
# Loop through and remove specific docker-related packages if they are installed
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do 
    sudo apt-get remove $pkg -y; 
done

# Update the package lists for upgrades and new package installations
sudo apt-get update -y

# Install necessary packages for fetching files over HTTPS
sudo apt-get install ca-certificates curl -y

# Create a directory for apt keyrings and set permissions
sudo install -m 0755 -d /etc/apt/keyrings

# Download Docker's official GPG key and save it to the keyrings directory
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Set read permissions for the Docker GPG key for all users
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker's APT repository to the sources list of apt package manager
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the apt package list after adding new repository
sudo apt-get update -y

# Install Docker Engine, CLI, containerd, and Docker compose plugins
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Test Docker installation by running the hello-world container
docker run hello-world
```

### Building docker container

To build:
```bash
nohup docker build -t corcelio/vision:orchestrator-1.0.0 -f Dockerfile.orchestrator . > build.log 2>&1 &
```

To run:
```bash
docker run --gpus all --runtime=nvidia -p 6919:6919 corcelio/vision:orchestrator-1.0.0
```

If that doesn't work:
```bash
docker run --gpus all  -p 6919:6919 corcelio/vision:orchestrator-1.0.0
```


**Combined command**
```bash
docker build -t corcelio/vision:orchestrator-1.0.0 .
docker run --gpus all  -p 6919:6919 corcelio/vision:orchestrator-1.0.0
```

### Uploading to docker hub
Get your credentials ready for docker hub
```bash
docker login
```

```bash
docker push corcelio/vision:orchestrator-1.0.0
```


### Trouble shooting
If you run into any Cuda prbs during build/run (especially with the argyment --runtime=nvidia), make sure to do this, then restart the last steps :
```bash
sudo nano /etc/docker/daemon.json
```

-> Change it to this : (define the default-runtime)
```json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

```bash
sudo systemctl restart docker
```

-> If you still can't run the image using gpu, it's surely a problem with Nvidia Drivers, follow steps on this link
```bash
# make sure this generates a correct output (gpu is detected)
lspci -vv | grep -i nvidia

# install drivers
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