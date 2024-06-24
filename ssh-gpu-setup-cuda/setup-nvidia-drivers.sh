#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# Pre-configure debconf to automatically select the desired option for openssh-server
echo "openssh-server openssh-server/permit-root-login boolean true" | sudo debconf-set-selections
echo "openssh-server openssh-server/sshd_config select keep" | sudo debconf-set-selections

# Hold openssh-server to prevent it from being upgraded
sudo apt-mark hold openssh-server

# Forcefully configure all packages non-interactively
sudo dpkg --configure -a --force-confdef --force-confold

# Remove all previous installs
sudo apt purge -y nvidia*
sudo apt remove -y nvidia-*
sudo rm -f /etc/apt/sources.list.d/cuda*
sudo apt autoremove -y && sudo apt autoclean -y
sudo rm -rf /usr/local/cuda*

# Update & upgrade
sudo apt update && sudo apt upgrade -y

# Install cpp compilation libraries
sudo apt install -y g++ freeglut3-dev build-essential libx11-dev libxmu-dev libxi-dev libglu1-mesa libglu1-mesa-dev


# Get recommended drivers
sudo add-apt-repository -y ppa:graphics-drivers/ppa
sudo apt update -y
sudo apt install -y ubuntu-drivers-common
RECOMMENDED_DRIVER_VERSION=$(ubuntu-drivers devices 2>/dev/null | grep recommended | awk -F'-' '{print $3}')

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

# Install recommended drivers + utility libraries
if [ -n "$RECOMMENDED_DRIVER_VERSION" ]; then
    sudo apt-get install -y --allow-downgrades --allow-remove-essential --allow-change-held-packages libnvidia-common-$RECOMMENDED_DRIVER_VERSION libnvidia-gl-$RECOMMENDED_DRIVER_VERSION nvidia-driver-$RECOMMENDED_DRIVER_VERSION
    handle_broken_install
else
    echo "No recommended driver found."
    exit 1
fi

echo "============================================================"
echo "          Nvidia Drivers setup completed successfully.           "
echo "                   Rebooting system now.                   "
echo "============================================================"

# Reboot
sudo reboot now