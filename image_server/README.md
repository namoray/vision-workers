**Vision ComfyUI Inference Server**

RUNNING WITH ENV VARS:


### `VRAM_MODE` : str

Options:

- `--low-vram` - Optimised for low vram usage of < 3GB - slowest
- `--normal-vram` - Swaps models in and out of vram / CPU memory - Still low memory usage but quicker than the above
- `--high-vram` - Keep all model weights on VRAM - quicker inference but more memory usage
- `--gpu-only` - Keep everything on VRAM - quickest inference but highest memory usage
- `--cpu` - don't do this :D

Keep the `--`'s in there!


### `WARMUP` : bool
- `true` - runs all models once to load everything, so subsequent generation times are quicker. 
- `false` - doesn't do that :D


### `PORT` : int 
The port to run the server on (default 6919)

### `DEVICE` : int
The Device to use for the image server (each image server can only use 1) (default 0)

### Some methods to use the server
- Use a 4090 with --normal-vram or --low-vram, to run everything on one machine. Have WARMUP true to prepare all models in advance
- USe an A100 or similar with --high-vram or --gpu-only, and have WARMUP true
- Use a 4090 with --high-vram/ --gpu-only, WARMUP FALSE, and only use the server with certain models. For example, use a load balancer to direct all `proteus` requests to this server, and then make another 4090 for playground, etc - depending on what you want to support.