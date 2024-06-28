
# Creating GPU Instance Guide

This guide provides instructions on how to create public/private SSH keys, set up a GPU instance, and SSH into your machine. We recommend using Oblivus or TensorDock as we have tested our setup on them.

## Generating SSH Keys

To create a new SSH key pair, follow these steps:

1. Open your terminal.
2. Generate the SSH key pair using the following command:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```
3. When prompted to enter a file in which to save the key, press Enter. This will save the key in the default location (`~/.ssh/id_rsa`).
4. You'll be asked to enter a passphrase. You can leave this blank for no passphrase, or enter a secure passphrase for added security.

The public key will be saved as `id_rsa.pub` and the private key as `id_rsa`.

## GPU Providers examples

We recommend using the following providers :

- [Oblivus](https://www.oblivus.com)
- [TensorDock](https://www.tensordock.com)

## Setting Up Your GPU Instance

When setting up your GPU instance, make sure to:

1. **Select GPU Type:** Choose the GPU type that suits your needs (e.g., NVIDIA Tesla V100, A100).
2. **Set Location:** Select a location that is closest to you or your user base for lower latency.
3. **Configure RAM and Disk:** Allocate sufficient RAM and disk space based on your requirements.
4. **Link Your Public Key:** During the setup process, make sure to link your public key (`id_rsa.pub`) to the instance. This will allow you to SSH into the machine.

## SSH into Your Machine

Once your instance is set up, use your private key to SSH into your machine. Here’s how:

1. Open your terminal.
2. Use the `ssh` command with your private key to access the instance:
   ```bash
   ssh -i ~/.ssh/id_rsa your_username@your_instance_ip
   ```
   Replace `your_username` with your instance username and `your_instance_ip` with the public IP address of your GPU instance.
   For Oblivus, username is usualy "root" and for TensorDock it's "user"

If you set a passphrase for your private key, you will be prompted to enter it.

Congratulations! You are now connected to your GPU instance.
