#!/bin/bash

usage() {
  echo "Usage: $0 -h <SSH_HOST> -k <SSH_KEY> [-u <SSH_USER>] [-p <SSH_PORT>]"
  exit 1
}

# Default values
SSH_USER="root"
SSH_PORT="22"

while getopts ":h:k:u:p:" opt; do
  case ${opt} in
    h)
      SSH_HOST=$OPTARG
      ;;
    k)
      SSH_KEY=$OPTARG
      ;;
    u)
      SSH_USER=$OPTARG
      ;;
    p)
      SSH_PORT=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

if [ -z "$SSH_HOST" ] || [ -z "$SSH_KEY" ]; then
  usage
fi

echo "Installing env on $SSH_HOST"

SSH_CMD="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST"

wait_for_reboot() {
  local timeout=300
  local interval=5
  local elapsed=0

  echo "Waiting for machine to reboot..."

  while ! ping -c 1 -W 1 $SSH_HOST &> /dev/null; do
    sleep $interval
    elapsed=$((elapsed + interval))
    if [ $elapsed -ge $timeout ]; then
      echo "Timeout while waiting for machine to reboot. Exiting."
      exit 1
    fi
  done

  echo "Machine is back online. Waiting for SSH to be available..."
  elapsed=0

  while ! ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST "echo SSH is up" &> /dev/null; do
    sleep $interval
    elapsed=$((elapsed + interval))
    if [ $elapsed -ge $timeout ]; then
      echo "Timeout while waiting for SSH to be available. Exiting."
      exit 1
    fi
  done

  echo "SSH is available. Continuing with the setup."
}

run_script() {
  local script_path=$1
  scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -P $SSH_PORT $script_path $SSH_USER@$SSH_HOST:~
  script_name=$(basename $script_path)
  $SSH_CMD "chmod +x ~/$script_name && ~/$script_name"
  sleep 5
}

start_time=$(date +%s)
run_script "setup-nvidia-drivers.sh"
wait_for_reboot
run_script "setup-cuda-toolkit-and-cudnn.sh"
wait_for_reboot
run_script "setup-docker-nvidia-tools.sh"

# Test nvidia-smi command (drivers)
if output_nvidia_smi=$(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST "source ~/.bashrc; nvidia-smi"); then
  echo "nvidia-smi command succeeded."
  echo "Output of nvidia-smi:"
  echo "$output_nvidia_smi"
else
  echo "nvidia-smi command failed."
  exit 1
fi

sleep 2

# Test nvcc --version command (toolkit)
if output_nvcc=$(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST "source ~/.bashrc; export PATH=/usr/local/cuda-11.8/bin:\$PATH; nvcc --version"); then
  echo "nvcc --version command succeeded."
  echo "Output of nvcc --version:"
  echo "$output_nvcc"
else
  echo "nvcc --version command failed."
  exit 1
fi

end_time=$(date +%s)
total_time=$((end_time - start_time))

# Print pretty message if all tests pass
echo "============================================================"
echo "          All operations completed successfully.           "
echo "           NVIDIA drivers and CUDA toolkit are installed.           "
echo "============================================================"
echo
echo "Total time taken: $((total_time / 60)) minutes and $((total_time % 60)) seconds"