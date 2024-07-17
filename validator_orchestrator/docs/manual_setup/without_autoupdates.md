
# Vision Orchestrator Server Setup

To run the server on bare metal, you will need Nvidia drivers, CUDA toolkit, and Docker.

## Prerequisites

1. [Prerequisites](../../../generic_docs/prerequisites.md)


## Pull the Docker Image

```bash
docker pull corcelio/vision:orchestrator-latest
```

## Running the Server

The server uses port 6919 to communicate with the LLM and image servers it spins up locally.

**Note:** Ensure that port 6919 is not used by another application on this GPU!

Port 6919 does not need to be exposed. Instead, port 6920 should be exposed (or any other port you choose if you run using a different one).

Run the server using the following command:

```bash
./launch_orchestrator.sh
```

Or edit the script to your liking.

### Specify which GPU

```bash
./launch_orchestrator.sh --device 0
```

### Troubleshooting

If that doesn't run properly, or you get nvidia runtime issues, try this:

```bash
./launch_orchestrator.sh --nvidia-runtime
```

Optionally specifying your GPU.

For further troubleshooting, refer to the [troubleshooting guide](../../../generic_docs/troubleshooting.md).
