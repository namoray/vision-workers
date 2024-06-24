
#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

handle_broken_install() {
  sudo apt --fix-broken install -y
  if [ $? -ne 0 ]; then
    conflicting_packages=$(sudo dpkg -l | grep -E 'nvidia-kernel-common|nvidia-compute-utils|nvidia-firmware' | awk '{print $2}')
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
}

# add nvidia repository
sudo wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /"

# fix broken installs
sudo apt --fix-broken install -y
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y

handle_broken_install

# install cuda 11.8 toolkit
sudo apt install cuda-11-8 -y

# setup env variables
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
sudo ldconfig


# install cudnn
CUDNN_TAR_FILE="cudnn-linux-x86_64-8.7.0.84_cuda11-archive.tar.xz"
sudo wget https://developer.download.nvidia.com/compute/redist/cudnn/v8.7.0/local_installers/11.8/${CUDNN_TAR_FILE}
sudo mkdir -p /usr/local/cuda-11.8/include
sudo mkdir -p /usr/local/cuda-11.8/lib64
sudo tar -xvf ${CUDNN_TAR_FILE}
sudo mv cudnn-linux-x86_64-8.7.0.84_cuda11-archive cuda

sudo cp -P cuda/include/cudnn.h /usr/local/cuda-11.8/include
sudo cp -P cuda/lib/libcudnn* /usr/local/cuda-11.8/lib64/
sudo chmod a+r /usr/local/cuda-11.8/lib64/libcudnn*

apt install -y npm && npm install -g pm2

echo "=================================================================="
echo "          Nvidia cuda toolkit setup completed successfully.           "
echo "                   Rebooting system now.                   "
echo "=================================================================="

sudo reboot now