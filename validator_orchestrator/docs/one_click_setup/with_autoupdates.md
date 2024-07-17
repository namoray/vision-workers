
# High-Level Setup Script for Cloud GPU Instances then launching autoupdates script and validator container

This guide explains how to use the provided scripts to set up a cloud GPU instance, install necessary drivers and tools, and clone the vision-workers git repository.
The script then launches autoupdates script, which will keep updating ressources (docker images, scripts)
The autoupdates script also starts validator container properly

## Prerequisites

- Access to a cloud service provider offering GPU instances (e.g., Oblivious, TensorDock). (details on [how to create a GPU machine on Oblivus/TensorDock](../../../generic_docs/create-gpu-instance.md))
- An SSH key pair for secure login to the instance.

## Steps to Use the Scripts
THESE STEPS BELOW ARE RUN ON YOUR LOCAL MACHINE / SOME MACHINE THAT IS NOT THE GPU

### Step 1: Checkout to main branch

1. **On your local machine, checkout to the main branch, and go inside ssh-gpu-setup-cuda**:
   ```bash
   cd ssh-gpu-setup-cuda
   ```

2. **Make the scripts executable**:
   ```bash
   chmod +x meta-setup.sh setup-run-autoupdates.sh
   ```

### Step 2: Run the High-Level Setup Script

1. **Execute the script**: Run the `setup-run-autoupdates.sh` script with the required arguments.
   ```bash
   ./setup-run-autoupdates.sh -h <SSH_HOST> -k <SSH_KEY> -r <GIT_REPO> [-b <BRANCH_NAME>] [-u <SSH_USER>] [-p <SSH_PORT>] [-o <ORCHESTRATOR_IMAGE>] [-l <LLM_IMAGE>] [-i <IMAGE_SERVER_IMAGE>]
   ```
   ```bash
   Mandatory : 
   <SSH_HOST> : IP of your gpu machine
   <SSH_KEY> : Path to the private ssh key you previously generated
   <GIT_REPO> : "github.com/namoray/vison-workers"

   Optional :
   <SSH_USER> : username on gpu machine (usually "root" for Oblivus and "user" for TensorDock)
   <SSH_PORT> : port used for ssh connection (usually 22)

   These are mostly for devs : 
   <ORCHESTRATOR_IMAGE> : orchestrator docker image
   <LLM_IMAGE> : llm server docker image
   <IMAGE_SERVER_IMAGE> : image server docker image
   ```
   When asked for a github PAT, leave it blanc (this part is for devs)
   For docker username and password, it is recommended to provide them in order to avoid docker pull rate limit issues

### Example Usage

```bash
./setup-run-autoupdates.sh -h 192.168.1.100 -k ~/.ssh/id_rsa -r github.com/namoray/vison-workers
```

### Manually checking logs
You can always ssh to your gpu machine, and use
```bash
pm2 list
```

to see the state of your autoupdates process
```bash
pm2 logs autoupdates
```
