**Vision LLM inference server**


Under the hood, the server uses the port 6919 to communicate with the llm and image servers it spins up locally.

Please make sure port 6919 is not used by another application on this GPU!

This port (6919) DOES NOT need to be exposed. Instead, 6920 should be exposed (or whatever port you select if you run using a different one)

## Running the docker image

Here's just an example command
```bash
docker pull corcelio/ml:orchestrator
docker run corcelio/ml:image_server
```

If that doesn't run properly, try adding these flags
`--gpus all`
`--runtime=nvidia`

Or you can specify some extra env vars if you need them
```bash
docker run -p 6920:6920 -e PORT=6920 -e CUDA_VISIBLE_DEVICES=0 DEVICE=0 corcelio/ml:image_server
```
DEVICE is for the image service, CUDA_VISIBLE_DEVICES is for the LLM server. 
Only one ever runs at a time, so using the default of 0 for both is more than fine