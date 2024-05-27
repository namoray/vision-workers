**Vision LLM inference server**




### Install docker
[docker readme](../../generic_docs/install_docker.md)

### Pull the image
```bash
docker pull corcelio/vision:orchestrator-latest
```
### Install conda
I recommend conda for an easy installation of nvidia-toolkit
[Conda installation](../../generic_docs/install_conda.md)

### Install nvidia stuff
[nvidia readme](../../generic_docs/install_nvidia_stuff.md)



### Running the server
Under the hood, the server uses the port 6919 to communicate with the llm and image servers it spins up locally.

Please make sure port 6919 is not used by another application on this GPU!

This port (6919) DOES NOT need to be exposed. Instead, 6920 should be exposed (or whatever port you select if you run using a different one)

## Running the docker image

Here's just an example command
```bash
docker pull corcelio/vision:orchestrator-latest
```

Or you can specify some extra env vars if you need them
```bash
docker run -p 6920:6920 -e PORT=6920 -e CUDA_VISIBLE_DEVICES=0 -e DEVICE=0 --gpus '"device=0"' --runtime=nvidia corcelio/vision:orchestrator-latest
```
DEVICE is for the image service, CUDA_VISIBLE_DEVICES is for the LLM server. 
Only one ever runs at a time, so using the default of 0 for both is more than fine


If that doesn't run properly, try removing the flag
`--runtime=nvidia`

## [Troubleshooting](../../generic_docs/troubleshooting.md)