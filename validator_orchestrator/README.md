**Vision LLM inference server**


Under the hood, the server uses the port 6919 to communicate with the llm and image servers it spins up locally.

Please make sure port 6919 is not used by another application on this GPU!

This port (6919) DOES NOT need to be exposed. Instead, 6920 should be exposed (or whatever port you select if you run using a different one)

## Running the docker image

Here's an example command to run it

```bash
docker pull corcelio/ml:orchestrator
```

```bash
docker run -p 6920:6920 -e PORT=6920 -e CUDA_VISIBLE_DEVICES=0 -e DEVICE=0 --gpus '"device=0"' --runtime=nvidia corcelio/ml:orchestrator
```
DEVICE is for the image service, CUDA_VISIBLE_DEVICES is for the LLM server. 
Only one ever runs at a time, so using the default of 0 for both is more than fine


If that doesn't run properly, try removing the flag
`--runtime=nvidia`

