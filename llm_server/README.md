**Vision LLM inference server**

RUNNING WITH ENV VARS:

### `PORT` : int 
The port to run the server on (default 6919)

### `CUDA_VISIBLE_DEVICES` : str
The Device to use for the vllm server. If not specified, will use cuda:0

Some options:

CUDA_VISIBLE_DEVICES=0,1,2,3
CUDA_VISIBLE_DEVICES=2
CUDA_VISIBLE_DEVICES=3,4


## Running the docker image

Here's just an example command
```bash
docker pull corcelio/ml:llm_server
docker run -p 6920:6920 --gpus '"device=0"' -e PORT=6920 --runtime=nvidia -e CUDA_VISIBLE_DEVICES=0 corcelio/ml:llm_server
```

If that doesn't run properly, try removing the flag
`--runtime=nvidia`

