**Vision LLM inference server**

In order to run the server on bare metal, you will need docker!

### Install docker
[docker readme](../../generic_docs/install_docker.md)

### Pull the image
```bash
docker pull corcelio/vision:llm_server-latest
```
### Install conda
I recommend conda for an easy installation of nvidia-toolkit
[Conda installation](../../generic_docs/install_conda.md)

### Install nvidia stuff
[nvidia readme](../../generic_docs/install_nvidia_stuff.md)

### Running the image

RUNNING WITH ENV VARS:

### `PORT` : int 
The port to run the server on (default 6919). The ports 6900-6919 are exposed by default, so pick one of those if you can!

### `CUDA_VISIBLE_DEVICES` : str
The Device to use for the vllm server. If not specified, will use cuda:0

Some options:

CUDA_VISIBLE_DEVICES=0,1,2,3
CUDA_VISIBLE_DEVICES=2
CUDA_VISIBLE_DEVICES=3,4

### `MODEL` : str
Model to use. E.g. `TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ`

### `HALF_PRECISION` : bool
Whether to use half precision E.g.: `true`

### `REVISION` : str
which revision of the model to use e.g.: `gptq-8bit-128g-actorder_True`


## Running the docker image

Here's just an example command
```bash
docker run -p 6919:6919 --gpus '"device=0"' --runtime=nvidia -e PORT=6919 -e MODEL=TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ -e HALF_PRECISION=true -e REVISION=gptq-8bit-128g-actorder_True -e CUDA_VISIBLE_DEVICES=0 corcelio/vision:llm_server-latest
```

If that doesn't run properly, try removing the flag
`--runtime=nvidia`

