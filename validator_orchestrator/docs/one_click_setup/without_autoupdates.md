
# High-Level Setup Script for Cloud GPU Instances and Launching Auto-Updates Script and Validator Container

This guide explains how to use the provided scripts to set up a cloud GPU instance, install necessary drivers and tools, and clone the vision-workers Git repository. The script then launches an auto-updates script, which will keep updating resources (Docker images, scripts). The auto-updates script also starts the validator container properly.

## Prerequisites

- Access to a cloud service provider offering GPU instances (e.g., Oblivus, TensorDock). (details on [how to create a GPU machine on Oblivus/TensorDock](../../../generic_docs/create-gpu-instance.md))
- An SSH key pair for secure login to the instance.

## Steps to Use the Scripts

THESE STEPS BELOW ARE RUN ON YOUR LOCAL MACHINE / SOME MACHINE THAT IS NOT THE GPU
### Step 1: Checkout to the Main Branch

1. **On your local machine, Checkout to the main branch and go inside ssh-gpu-setup-cuda**:
   ```bash
   git clone https://github.com/namoray/vision-workers.git
   cd vision-workers/ssh-gpu-setup-cuda
   ```

2. **Make the scripts executable**:
   ```bash
   chmod +x meta-setup.sh setup-run-autoupdates.sh
   ```

### Step 2: Run the High-Level Setup Script

1. **Execute the script**: Run the `meta-setup.sh` script with the required arguments.
   ```bash
   ./meta-setup.sh -h <SSH_HOST> -k <SSH_KEY> -r <GIT_REPO> [-b <BRANCH_NAME>] [-u <SSH_USER>] [-p <SSH_PORT>]
   ```
   - `<SSH_HOST>`: IP of your GPU machine
   - `<SSH_KEY>`: Path to the private SSH key you previously generated
   - `<GIT_REPO>`: "github.com/namoray/vision-workers"

   When asked for a PAT, leave it blank (this part is for developers).

### Example usages for Oblivus & TensorDock providers
1. **For Oblivus**: Oblivus exposes the port 22 and uses "root" as user, so no need to change those. The command looks like this 
   ```bash
   ./meta-setup.sh -h 192.168.1.100 -k ~/.ssh/id_rsa -r github.com/namoray/vision-workers
   ```
2. **For TensorDock**: Here you need to use the flags -u (for user) and -p (for port) according to your machine. It's usually "-u user -p 11308"
   ```bash
   ./meta-setup.sh -h 192.168.1.100 -k ~/.ssh/id_rsa -r github.com/namoray/vision-workers -u user -p 11308 
   ```

### Step 3: SSH to Your Machine and Run the Orchestrator

Under the hood, the server uses port 6919 to communicate with the LLM and image servers it spins up locally.<br>
Please make sure port 6919 is not used by another application on this GPU!<br>
This port (6919) DOES NOT need to be exposed. Instead, 6920 should be exposed (or whatever port you select if you run using a different one).<br>
<br>
You can either run using this command:
```bash
./launch_orchestrator.sh
```
Or edit the script to your liking.

### Specify Which GPU

```bash
./launch_orchestrator.sh --device 0
```

### Troubleshooting

If the script doesn't run properly, try this:
```bash
./launch_orchestrator.sh --no-runtime-flag
```

Optionally specifying your GPU.

For further troubleshooting, see here:
## [Troubleshooting](../../../generic_docs/troubleshooting.md)
